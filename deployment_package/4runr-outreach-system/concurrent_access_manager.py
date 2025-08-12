#!/usr/bin/env python3
"""
Concurrent Access Manager for Lead Database System

This module provides thread-safe operations, deadlock detection,
and concurrent access coordination for the lead database system.

Features:
- Thread-safe database operations
- Deadlock detection and recovery
- Operation queuing and prioritization
- Resource locking and coordination
- Performance monitoring for concurrent operations
"""

import threading
import time
import queue
import logging
import sqlite3
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import functools
import weakref
from contextlib import contextmanager

from database_connection_pool import get_connection_pool, DatabaseConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperationPriority(Enum):
    """Priority levels for database operations"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class LockType(Enum):
    """Types of locks for database resources"""
    SHARED = "shared"
    EXCLUSIVE = "exclusive"

@dataclass
class OperationRequest:
    """Represents a database operation request"""
    operation_id: str
    operation_type: str
    priority: OperationPriority
    requested_at: datetime
    timeout: int
    callback: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    thread_id: int = field(default_factory=threading.get_ident)
    
    def __lt__(self, other):
        """Enable priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Higher priority first
        return self.requested_at < other.requested_at  # Earlier requests first

@dataclass
class ResourceLock:
    """Represents a lock on a database resource"""
    resource_id: str
    lock_type: LockType
    owner_thread: int
    acquired_at: datetime
    operation_id: str
    timeout: Optional[datetime] = None

@dataclass
class DeadlockInfo:
    """Information about a detected deadlock"""
    deadlock_id: str
    detected_at: datetime
    involved_threads: List[int]
    involved_operations: List[str]
    resolution_action: str
    victim_operation: Optional[str] = None

class ConcurrentAccessManager:
    """
    Manages concurrent access to the lead database with deadlock detection
    and operation coordination
    """
    
    def __init__(self, 
                 db_path: str,
                 max_concurrent_operations: int = 10,
                 operation_timeout: int = 300,
                 deadlock_detection_interval: int = 5,
                 enable_operation_queuing: bool = True):
        """
        Initialize the concurrent access manager
        
        Args:
            db_path: Path to the database
            max_concurrent_operations: Maximum concurrent operations allowed
            operation_timeout: Default timeout for operations (seconds)
            deadlock_detection_interval: Interval for deadlock detection (seconds)
            enable_operation_queuing: Enable operation queuing
        """
        self.db_path = db_path
        self.max_concurrent_operations = max_concurrent_operations
        self.operation_timeout = operation_timeout
        self.deadlock_detection_interval = deadlock_detection_interval
        self.enable_operation_queuing = enable_operation_queuing
        
        # Get connection pool
        self.connection_pool = get_connection_pool(db_path)
        
        # Operation management
        self._operation_queue = queue.PriorityQueue()
        self._active_operations: Dict[str, OperationRequest] = {}
        self._operation_results: Dict[str, Any] = {}
        self._operation_errors: Dict[str, Exception] = {}
        
        # Resource locking
        self._resource_locks: Dict[str, List[ResourceLock]] = {}
        self._lock_waiters: Dict[str, List[OperationRequest]] = {}
        
        # Thread coordination
        self._access_lock = threading.RLock()
        self._operation_semaphore = threading.Semaphore(max_concurrent_operations)
        self._shutdown_event = threading.Event()
        
        # Deadlock detection
        self._deadlock_detector_thread = None
        self._detected_deadlocks: List[DeadlockInfo] = []
        
        # Statistics
        self._stats = {
            'operations_queued': 0,
            'operations_completed': 0,
            'operations_failed': 0,
            'operations_timeout': 0,
            'deadlocks_detected': 0,
            'deadlocks_resolved': 0,
            'average_operation_time': 0.0,
            'peak_concurrent_operations': 0
        }
        
        # Start background threads
        self._start_background_threads()
    
    def _start_background_threads(self):
        """Start background threads for operation processing and deadlock detection"""
        # Operation processor thread
        self._processor_thread = threading.Thread(
            target=self._operation_processor, 
            daemon=True,
            name="OperationProcessor"
        )
        self._processor_thread.start()
        
        # Deadlock detector thread
        self._deadlock_detector_thread = threading.Thread(
            target=self._deadlock_detector,
            daemon=True,
            name="DeadlockDetector"
        )
        self._deadlock_detector_thread.start()
        
        logger.info("Started concurrent access manager background threads")
    
    def _operation_processor(self):
        """Background thread that processes queued operations"""
        while not self._shutdown_event.is_set():
            try:
                # Get next operation from queue (with timeout)
                try:
                    operation = self._operation_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Acquire semaphore for concurrent operation limit
                if self._operation_semaphore.acquire(timeout=operation.timeout):
                    try:
                        # Process the operation
                        self._execute_operation(operation)
                    finally:
                        self._operation_semaphore.release()
                else:
                    # Operation timed out waiting for semaphore
                    self._handle_operation_timeout(operation)
                
                self._operation_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in operation processor: {e}")
    
    def _execute_operation(self, operation: OperationRequest):
        """Execute a database operation with proper locking and error handling"""
        start_time = time.time()
        
        try:
            with self._access_lock:
                self._active_operations[operation.operation_id] = operation
                current_active = len(self._active_operations)
                if current_active > self._stats['peak_concurrent_operations']:
                    self._stats['peak_concurrent_operations'] = current_active
            
            logger.debug(f"Executing operation {operation.operation_id} ({operation.operation_type})")
            
            # Execute the operation callback
            result = operation.callback(*operation.args, **operation.kwargs)
            
            # Store result
            with self._access_lock:
                self._operation_results[operation.operation_id] = result
                self._stats['operations_completed'] += 1
            
            execution_time = time.time() - start_time
            self._update_average_operation_time(execution_time)
            
            logger.debug(f"Completed operation {operation.operation_id} in {execution_time:.3f}s")
            
        except Exception as e:
            # Store error
            with self._access_lock:
                self._operation_errors[operation.operation_id] = e
                self._stats['operations_failed'] += 1
            
            logger.error(f"Operation {operation.operation_id} failed: {e}")
            
        finally:
            # Clean up operation tracking
            with self._access_lock:
                if operation.operation_id in self._active_operations:
                    del self._active_operations[operation.operation_id]
    
    def _handle_operation_timeout(self, operation: OperationRequest):
        """Handle operation timeout"""
        with self._access_lock:
            self._operation_errors[operation.operation_id] = TimeoutError(
                f"Operation {operation.operation_id} timed out after {operation.timeout} seconds"
            )
            self._stats['operations_timeout'] += 1
        
        logger.warning(f"Operation {operation.operation_id} timed out")
    
    def _update_average_operation_time(self, execution_time: float):
        """Update the average operation time statistic"""
        with self._access_lock:
            completed = self._stats['operations_completed']
            if completed == 1:
                self._stats['average_operation_time'] = execution_time
            else:
                # Running average
                current_avg = self._stats['average_operation_time']
                self._stats['average_operation_time'] = (
                    (current_avg * (completed - 1) + execution_time) / completed
                )
    
    def _deadlock_detector(self):
        """Background thread that detects and resolves deadlocks"""
        while not self._shutdown_event.is_set():
            try:
                time.sleep(self.deadlock_detection_interval)
                self._detect_and_resolve_deadlocks()
            except Exception as e:
                logger.error(f"Error in deadlock detector: {e}")
    
    def _detect_and_resolve_deadlocks(self):
        """Detect and resolve deadlocks in the system"""
        with self._access_lock:
            # Build wait-for graph
            wait_graph = self._build_wait_graph()
            
            # Detect cycles (deadlocks)
            deadlocks = self._find_cycles_in_wait_graph(wait_graph)
            
            # Resolve detected deadlocks
            for deadlock_threads in deadlocks:
                self._resolve_deadlock(deadlock_threads)
    
    def _build_wait_graph(self) -> Dict[int, List[int]]:
        """Build a wait-for graph to detect deadlocks"""
        wait_graph = {}
        
        # For each resource, check which threads are waiting
        for resource_id, locks in self._resource_locks.items():
            if not locks:
                continue
            
            # Get current lock holders
            lock_holders = [lock.owner_thread for lock in locks]
            
            # Get threads waiting for this resource
            waiters = self._lock_waiters.get(resource_id, [])
            waiter_threads = [op.thread_id for op in waiters]
            
            # Each waiter is waiting for each lock holder
            for waiter_thread in waiter_threads:
                if waiter_thread not in wait_graph:
                    wait_graph[waiter_thread] = []
                
                for holder_thread in lock_holders:
                    if holder_thread != waiter_thread:
                        wait_graph[waiter_thread].append(holder_thread)
        
        return wait_graph
    
    def _find_cycles_in_wait_graph(self, wait_graph: Dict[int, List[int]]) -> List[List[int]]:
        """Find cycles in the wait-for graph (indicating deadlocks)"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in wait_graph.get(node, []):
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
        
        for node in wait_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _resolve_deadlock(self, deadlock_threads: List[int]):
        """Resolve a deadlock by aborting one of the involved operations"""
        deadlock_id = str(uuid.uuid4())
        
        # Find operations involved in the deadlock
        involved_operations = []
        for thread_id in deadlock_threads:
            for op_id, operation in self._active_operations.items():
                if operation.thread_id == thread_id:
                    involved_operations.append(op_id)
        
        if not involved_operations:
            return
        
        # Choose victim operation (lowest priority, or oldest if same priority)
        victim_operation = self._choose_deadlock_victim(involved_operations)
        
        # Record deadlock information
        deadlock_info = DeadlockInfo(
            deadlock_id=deadlock_id,
            detected_at=datetime.now(),
            involved_threads=deadlock_threads,
            involved_operations=involved_operations,
            resolution_action="abort_operation",
            victim_operation=victim_operation
        )
        
        self._detected_deadlocks.append(deadlock_info)
        self._stats['deadlocks_detected'] += 1
        
        # Abort the victim operation
        if victim_operation in self._active_operations:
            operation = self._active_operations[victim_operation]
            self._operation_errors[victim_operation] = RuntimeError(
                f"Operation aborted due to deadlock resolution (deadlock_id: {deadlock_id})"
            )
            
            # Release any locks held by this operation
            self._release_operation_locks(victim_operation)
            
            # Remove from active operations
            del self._active_operations[victim_operation]
            
            self._stats['deadlocks_resolved'] += 1
            
            logger.warning(f"Resolved deadlock {deadlock_id} by aborting operation {victim_operation}")
    
    def _choose_deadlock_victim(self, operation_ids: List[str]) -> str:
        """Choose which operation to abort to resolve a deadlock"""
        # Get operation details
        operations = []
        for op_id in operation_ids:
            if op_id in self._active_operations:
                operations.append((op_id, self._active_operations[op_id]))
        
        if not operations:
            return operation_ids[0]  # Fallback
        
        # Sort by priority (lowest first) and then by start time (oldest first)
        operations.sort(key=lambda x: (x[1].priority.value, x[1].requested_at))
        
        return operations[0][0]  # Return the operation ID of the victim
    
    def _release_operation_locks(self, operation_id: str):
        """Release all locks held by an operation"""
        for resource_id, locks in list(self._resource_locks.items()):
            # Remove locks owned by this operation
            self._resource_locks[resource_id] = [
                lock for lock in locks 
                if lock.operation_id != operation_id
            ]
            
            # Clean up empty lock lists
            if not self._resource_locks[resource_id]:
                del self._resource_locks[resource_id]
    
    @contextmanager
    def acquire_resource_lock(self, 
                            resource_id: str, 
                            lock_type: LockType = LockType.EXCLUSIVE,
                            timeout: int = 30,
                            operation_id: str = None):
        """
        Acquire a lock on a database resource
        
        Args:
            resource_id: Identifier for the resource to lock
            lock_type: Type of lock to acquire
            timeout: Timeout for acquiring the lock
            operation_id: Operation ID requesting the lock
        """
        operation_id = operation_id or str(uuid.uuid4())
        thread_id = threading.get_ident()
        
        lock = ResourceLock(
            resource_id=resource_id,
            lock_type=lock_type,
            owner_thread=thread_id,
            acquired_at=datetime.now(),
            operation_id=operation_id,
            timeout=datetime.now() + timedelta(seconds=timeout)
        )
        
        # Try to acquire the lock
        acquired = self._try_acquire_lock(lock, timeout)
        
        if not acquired:
            raise TimeoutError(f"Could not acquire {lock_type.value} lock on {resource_id} within {timeout} seconds")
        
        try:
            logger.debug(f"Acquired {lock_type.value} lock on {resource_id} for operation {operation_id}")
            yield lock
        finally:
            # Release the lock
            self._release_lock(lock)
            logger.debug(f"Released {lock_type.value} lock on {resource_id} for operation {operation_id}")
    
    def _try_acquire_lock(self, lock: ResourceLock, timeout: int) -> bool:
        """Try to acquire a resource lock"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._access_lock:
                if self._can_acquire_lock(lock):
                    # Acquire the lock
                    if lock.resource_id not in self._resource_locks:
                        self._resource_locks[lock.resource_id] = []
                    
                    self._resource_locks[lock.resource_id].append(lock)
                    return True
                else:
                    # Add to waiters if not already there
                    if lock.resource_id not in self._lock_waiters:
                        self._lock_waiters[lock.resource_id] = []
                    
                    # Create a dummy operation request for waiting
                    dummy_op = OperationRequest(
                        operation_id=lock.operation_id,
                        operation_type="lock_wait",
                        priority=OperationPriority.NORMAL,
                        requested_at=datetime.now(),
                        timeout=timeout,
                        callback=lambda: None,
                        thread_id=lock.owner_thread
                    )
                    
                    if dummy_op not in self._lock_waiters[lock.resource_id]:
                        self._lock_waiters[lock.resource_id].append(dummy_op)
            
            # Wait a bit before retrying
            time.sleep(0.01)
        
        return False
    
    def _can_acquire_lock(self, requested_lock: ResourceLock) -> bool:
        """Check if a lock can be acquired"""
        existing_locks = self._resource_locks.get(requested_lock.resource_id, [])
        
        if not existing_locks:
            return True
        
        # Check compatibility
        for existing_lock in existing_locks:
            # Same thread can always acquire additional locks
            if existing_lock.owner_thread == requested_lock.owner_thread:
                continue
            
            # Exclusive locks are incompatible with any other lock
            if (existing_lock.lock_type == LockType.EXCLUSIVE or 
                requested_lock.lock_type == LockType.EXCLUSIVE):
                return False
            
            # Shared locks are compatible with other shared locks
            if (existing_lock.lock_type == LockType.SHARED and 
                requested_lock.lock_type == LockType.SHARED):
                continue
        
        return True
    
    def _release_lock(self, lock: ResourceLock):
        """Release a resource lock"""
        with self._access_lock:
            if lock.resource_id in self._resource_locks:
                # Remove the lock
                self._resource_locks[lock.resource_id] = [
                    l for l in self._resource_locks[lock.resource_id]
                    if not (l.owner_thread == lock.owner_thread and 
                           l.operation_id == lock.operation_id)
                ]
                
                # Clean up empty lock lists
                if not self._resource_locks[lock.resource_id]:
                    del self._resource_locks[lock.resource_id]
                
                # Remove from waiters
                if lock.resource_id in self._lock_waiters:
                    self._lock_waiters[lock.resource_id] = [
                        op for op in self._lock_waiters[lock.resource_id]
                        if op.operation_id != lock.operation_id
                    ]
                    
                    if not self._lock_waiters[lock.resource_id]:
                        del self._lock_waiters[lock.resource_id]
    
    def execute_operation(self, 
                         operation_type: str,
                         callback: Callable,
                         args: tuple = (),
                         kwargs: dict = None,
                         priority: OperationPriority = OperationPriority.NORMAL,
                         timeout: int = None,
                         wait_for_result: bool = True) -> Any:
        """
        Execute a database operation with concurrent access management
        
        Args:
            operation_type: Type of operation being performed
            callback: Function to execute
            args: Arguments for the callback
            kwargs: Keyword arguments for the callback
            priority: Operation priority
            timeout: Operation timeout (uses default if None)
            wait_for_result: Whether to wait for the operation result
            
        Returns:
            Operation result if wait_for_result is True, otherwise operation ID
        """
        kwargs = kwargs or {}
        timeout = timeout or self.operation_timeout
        
        operation = OperationRequest(
            operation_id=str(uuid.uuid4()),
            operation_type=operation_type,
            priority=priority,
            requested_at=datetime.now(),
            timeout=timeout,
            callback=callback,
            args=args,
            kwargs=kwargs
        )
        
        if self.enable_operation_queuing:
            # Queue the operation
            self._operation_queue.put(operation)
            
            with self._access_lock:
                self._stats['operations_queued'] += 1
            
            if wait_for_result:
                return self._wait_for_operation_result(operation.operation_id, timeout)
            else:
                return operation.operation_id
        else:
            # Execute immediately
            self._execute_operation(operation)
            
            if wait_for_result:
                return self._get_operation_result(operation.operation_id)
            else:
                return operation.operation_id
    
    def _wait_for_operation_result(self, operation_id: str, timeout: int) -> Any:
        """Wait for an operation to complete and return its result"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._access_lock:
                if operation_id in self._operation_results:
                    result = self._operation_results[operation_id]
                    del self._operation_results[operation_id]  # Clean up
                    return result
                
                if operation_id in self._operation_errors:
                    error = self._operation_errors[operation_id]
                    del self._operation_errors[operation_id]  # Clean up
                    raise error
            
            time.sleep(0.01)  # Small delay to avoid busy waiting
        
        raise TimeoutError(f"Operation {operation_id} did not complete within {timeout} seconds")
    
    def _get_operation_result(self, operation_id: str) -> Any:
        """Get the result of an operation (non-blocking)"""
        with self._access_lock:
            if operation_id in self._operation_results:
                result = self._operation_results[operation_id]
                del self._operation_results[operation_id]
                return result
            
            if operation_id in self._operation_errors:
                error = self._operation_errors[operation_id]
                del self._operation_errors[operation_id]
                raise error
        
        raise RuntimeError(f"Operation {operation_id} result not available")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get concurrent access manager statistics"""
        with self._access_lock:
            pool_stats = self.connection_pool.get_pool_stats()
            
            return {
                'concurrent_access_stats': dict(self._stats),
                'active_operations': len(self._active_operations),
                'queued_operations': self._operation_queue.qsize(),
                'active_locks': sum(len(locks) for locks in self._resource_locks.values()),
                'waiting_operations': sum(len(waiters) for waiters in self._lock_waiters.values()),
                'detected_deadlocks': len(self._detected_deadlocks),
                'connection_pool_stats': pool_stats
            }
    
    def get_deadlock_history(self) -> List[Dict[str, Any]]:
        """Get history of detected deadlocks"""
        return [
            {
                'deadlock_id': dl.deadlock_id,
                'detected_at': dl.detected_at.isoformat(),
                'involved_threads': dl.involved_threads,
                'involved_operations': dl.involved_operations,
                'resolution_action': dl.resolution_action,
                'victim_operation': dl.victim_operation
            }
            for dl in self._detected_deadlocks
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the concurrent access manager"""
        try:
            stats = self.get_stats()
            pool_health = self.connection_pool.health_check()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            # Check for high queue backlog
            if stats['queued_operations'] > self.max_concurrent_operations * 2:
                health_status = "warning"
                issues.append("High operation queue backlog")
            
            # Check for frequent deadlocks
            if stats['concurrent_access_stats']['deadlocks_detected'] > 10:
                health_status = "warning"
                issues.append("Frequent deadlocks detected")
            
            # Check operation success rate
            total_ops = (stats['concurrent_access_stats']['operations_completed'] + 
                        stats['concurrent_access_stats']['operations_failed'])
            if total_ops > 0:
                success_rate = stats['concurrent_access_stats']['operations_completed'] / total_ops
                if success_rate < 0.95:
                    health_status = "warning"
                    issues.append("Low operation success rate")
            
            # Include connection pool health
            if pool_health['status'] != 'healthy':
                health_status = pool_health['status']
                issues.extend(pool_health['issues'])
            
            return {
                'status': health_status,
                'issues': issues,
                'stats': stats,
                'connection_pool_health': pool_health,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'issues': [f"Health check failed: {str(e)}"],
                'last_check': datetime.now().isoformat()
            }
    
    def shutdown(self):
        """Shutdown the concurrent access manager"""
        logger.info("Shutting down concurrent access manager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for background threads to finish
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=5)
        
        if self._deadlock_detector_thread and self._deadlock_detector_thread.is_alive():
            self._deadlock_detector_thread.join(timeout=5)
        
        # Clear all data structures
        with self._access_lock:
            self._active_operations.clear()
            self._operation_results.clear()
            self._operation_errors.clear()
            self._resource_locks.clear()
            self._lock_waiters.clear()
        
        logger.info("Concurrent access manager shutdown complete")

# Decorator for thread-safe database operations
def thread_safe_operation(operation_type: str, 
                         priority: OperationPriority = OperationPriority.NORMAL,
                         timeout: int = None,
                         resource_locks: List[str] = None):
    """
    Decorator to make database operations thread-safe
    
    Args:
        operation_type: Type of operation
        priority: Operation priority
        timeout: Operation timeout
        resource_locks: List of resources to lock
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the concurrent access manager (assumes it's available globally)
            # In practice, this would be injected or configured
            access_manager = kwargs.pop('_access_manager', None)
            if not access_manager:
                # Fallback to direct execution if no access manager
                return func(*args, **kwargs)
            
            # Define the operation callback
            def operation_callback():
                if resource_locks:
                    # Acquire resource locks
                    with contextlib.ExitStack() as stack:
                        for resource_id in resource_locks:
                            stack.enter_context(
                                access_manager.acquire_resource_lock(resource_id)
                            )
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            # Execute through the access manager
            return access_manager.execute_operation(
                operation_type=operation_type,
                callback=operation_callback,
                priority=priority,
                timeout=timeout
            )
        
        return wrapper
    return decorator

# Global concurrent access manager instance
_access_manager: Optional[ConcurrentAccessManager] = None
_access_manager_lock = threading.Lock()

def get_concurrent_access_manager(db_path: str = None, **kwargs) -> ConcurrentAccessManager:
    """Get the global concurrent access manager instance"""
    global _access_manager
    
    with _access_manager_lock:
        if _access_manager is None:
            if not db_path:
                raise ValueError("db_path is required for first access manager initialization")
            _access_manager = ConcurrentAccessManager(db_path, **kwargs)
        
        return _access_manager

def shutdown_concurrent_access_manager():
    """Shutdown the global concurrent access manager"""
    global _access_manager
    
    with _access_manager_lock:
        if _access_manager:
            _access_manager.shutdown()
            _access_manager = None