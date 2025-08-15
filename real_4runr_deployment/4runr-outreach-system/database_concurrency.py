#!/usr/bin/env python3
"""
Database Concurrency Management for Lead Database Integration.

This module provides comprehensive concurrent access safety including:
- Advanced database locking mechanisms
- Transaction management with rollback capabilities
- Connection pooling for multiple simultaneous agents
- Thread-safe operations with proper synchronization
- Deadlock detection and prevention
"""

import sqlite3
import threading
import time
import queue
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import weakref

from database_config import get_database_config, DatabaseConfig
from database_logger import database_logger, log_database_event


class LockType(Enum):
    """Types of database locks."""
    SHARED = "SHARED"
    EXCLUSIVE = "EXCLUSIVE"
    RESERVED = "RESERVED"


class TransactionIsolation(Enum):
    """Transaction isolation levels."""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


@dataclass
class ConnectionInfo:
    """Information about a database connection."""
    connection_id: str
    thread_id: int
    created_at: datetime
    last_used: datetime
    in_use: bool = False
    transaction_active: bool = False
    lock_type: Optional[LockType] = None
    
    def __post_init__(self):
        """Update last_used when connection info is accessed."""
        self.last_used = datetime.now()


@dataclass
class TransactionContext:
    """Context information for a database transaction."""
    transaction_id: str
    connection_id: str
    thread_id: int
    started_at: datetime
    isolation_level: TransactionIsolation
    operations: List[str] = field(default_factory=list)
    savepoints: List[str] = field(default_factory=list)
    
    def add_operation(self, operation: str):
        """Add an operation to the transaction log."""
        self.operations.append(f"{datetime.now().isoformat()}: {operation}")


class DatabaseConnectionPool:
    """Thread-safe database connection pool with advanced features."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize the connection pool.
        
        Args:
            config: Database configuration (uses default if None)
        """
        self.config = config or get_database_config()
        self.db_path = self.config.database_path
        
        # Connection pool
        self._pool = queue.Queue(maxsize=self.config.max_connections)
        self._connections: Dict[str, sqlite3.Connection] = {}
        self._connection_info: Dict[str, ConnectionInfo] = {}
        
        # Thread safety
        self._pool_lock = threading.RLock()
        self._connections_lock = threading.RLock()
        
        # Transaction management
        self._active_transactions: Dict[str, TransactionContext] = {}
        self._transaction_lock = threading.RLock()
        
        # Deadlock detection
        self._lock_wait_graph: Dict[int, List[int]] = {}
        self._deadlock_lock = threading.RLock()
        
        # Connection cleanup
        self._cleanup_thread = None
        self._shutdown_event = threading.Event()
        
        # Statistics
        self._stats = {
            'connections_created': 0,
            'connections_reused': 0,
            'transactions_started': 0,
            'transactions_committed': 0,
            'transactions_rolled_back': 0,
            'deadlocks_detected': 0,
            'lock_timeouts': 0
        }
        
        # Initialize pool
        self._initialize_pool()
        self._start_cleanup_thread()
        
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Database connection pool initialized with {self.config.max_connections} connections")
    
    def _initialize_pool(self):
        """Initialize the connection pool with connections."""
        with self._pool_lock:
            for _ in range(self.config.max_connections):
                conn = self._create_connection()
                if conn:
                    self._pool.put(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimizations."""
        try:
            # Create connection with optimizations
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode, we'll manage transactions manually
            )
            
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            # Apply SQLite optimizations
            pragmas = self.config.get_sqlite_pragmas()
            for pragma, value in pragmas.items():
                conn.execute(f"PRAGMA {pragma} = {value}")
            
            # Generate connection ID and store info
            connection_id = str(uuid.uuid4())[:8]
            
            with self._connections_lock:
                self._connections[connection_id] = conn
                self._connection_info[connection_id] = ConnectionInfo(
                    connection_id=connection_id,
                    thread_id=threading.get_ident(),
                    created_at=datetime.now(),
                    last_used=datetime.now()
                )
            
            self._stats['connections_created'] += 1
            
            # Store connection ID in connection object for tracking
            conn._connection_id = connection_id
            
            return conn
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to create database connection: {e}")
            return None
    
    def _start_cleanup_thread(self):
        """Start the connection cleanup thread."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_connections,
            daemon=True,
            name="DatabaseConnectionCleanup"
        )
        self._cleanup_thread.start()
    
    def _cleanup_connections(self):
        """Clean up idle connections periodically."""
        logger = logging.getLogger(__name__)
        
        while not self._shutdown_event.wait(60):  # Check every minute
            try:
                current_time = datetime.now()
                idle_threshold = timedelta(minutes=10)  # Close connections idle for 10+ minutes
                
                with self._connections_lock:
                    idle_connections = []
                    
                    for conn_id, info in self._connection_info.items():
                        if (not info.in_use and 
                            not info.transaction_active and
                            current_time - info.last_used > idle_threshold):
                            idle_connections.append(conn_id)
                    
                    for conn_id in idle_connections:
                        try:
                            conn = self._connections.get(conn_id)
                            if conn:
                                conn.close()
                                del self._connections[conn_id]
                                del self._connection_info[conn_id]
                                logger.debug(f"🧹 Cleaned up idle connection: {conn_id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Error cleaning up connection {conn_id}: {e}")
                
            except Exception as e:
                logger.error(f"❌ Error in connection cleanup: {e}")
    
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        Get a connection from the pool with timeout.
        
        Args:
            timeout: Timeout in seconds (uses config default if None)
            
        Yields:
            sqlite3.Connection: Database connection
        """
        timeout = timeout or self.config.connection_timeout
        connection = None
        connection_id = None
        
        try:
            # Get connection from pool
            try:
                connection = self._pool.get(timeout=timeout)
                connection_id = getattr(connection, '_connection_id', None)
                
                if connection_id:
                    with self._connections_lock:
                        if connection_id in self._connection_info:
                            self._connection_info[connection_id].in_use = True
                            self._connection_info[connection_id].last_used = datetime.now()
                
                self._stats['connections_reused'] += 1
                
            except queue.Empty:
                # Pool is empty, create new connection if possible
                connection = self._create_connection()
                if not connection:
                    raise RuntimeError("Could not create database connection")
                connection_id = getattr(connection, '_connection_id', None)
            
            # Verify connection is still valid
            try:
                connection.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is invalid, create a new one
                if connection_id:
                    with self._connections_lock:
                        self._connections.pop(connection_id, None)
                        self._connection_info.pop(connection_id, None)
                
                connection = self._create_connection()
                if not connection:
                    raise RuntimeError("Could not create database connection")
                connection_id = getattr(connection, '_connection_id', None)
            
            yield connection
            
        finally:
            # Return connection to pool
            if connection and connection_id:
                try:
                    # Mark as not in use
                    with self._connections_lock:
                        if connection_id in self._connection_info:
                            self._connection_info[connection_id].in_use = False
                            self._connection_info[connection_id].last_used = datetime.now()
                    
                    # Return to pool if pool has space
                    try:
                        self._pool.put_nowait(connection)
                    except queue.Full:
                        # Pool is full, close this connection
                        connection.close()
                        with self._connections_lock:
                            self._connections.pop(connection_id, None)
                            self._connection_info.pop(connection_id, None)
                
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"⚠️ Error returning connection to pool: {e}")
    
    @contextmanager
    def get_transaction(self, isolation_level: TransactionIsolation = TransactionIsolation.READ_COMMITTED):
        """
        Get a transactional connection with rollback support.
        
        Args:
            isolation_level: Transaction isolation level
            
        Yields:
            Tuple[sqlite3.Connection, str]: Connection and transaction ID
        """
        transaction_id = str(uuid.uuid4())[:8]
        
        with self.get_connection() as conn:
            connection_id = getattr(conn, '_connection_id', 'unknown')
            
            # Create transaction context
            transaction_context = TransactionContext(
                transaction_id=transaction_id,
                connection_id=connection_id,
                thread_id=threading.get_ident(),
                started_at=datetime.now(),
                isolation_level=isolation_level
            )
            
            with self._transaction_lock:
                self._active_transactions[transaction_id] = transaction_context
                
                # Mark connection as having active transaction
                if connection_id in self._connection_info:
                    self._connection_info[connection_id].transaction_active = True
            
            try:
                # Begin transaction
                conn.execute("BEGIN")
                transaction_context.add_operation("BEGIN TRANSACTION")
                self._stats['transactions_started'] += 1
                
                # Log transaction start
                log_database_event("database_operation", {"transaction_id": transaction_id}, {
                    "success": True,
                    "operation_type": "begin_transaction",
                    "isolation_level": isolation_level.value
                }, {
                    "operation_type": "transaction_management",
                    "performance_metrics": {"execution_time_ms": 0}
                })
                
                yield conn, transaction_id
                
                # Commit transaction
                conn.execute("COMMIT")
                transaction_context.add_operation("COMMIT TRANSACTION")
                self._stats['transactions_committed'] += 1
                
                # Log transaction commit
                log_database_event("database_operation", {"transaction_id": transaction_id}, {
                    "success": True,
                    "operation_type": "commit_transaction",
                    "operations_count": len(transaction_context.operations)
                }, {
                    "operation_type": "transaction_management",
                    "performance_metrics": {"execution_time_ms": 0}
                })
                
            except Exception as e:
                # Rollback transaction
                try:
                    conn.execute("ROLLBACK")
                    transaction_context.add_operation(f"ROLLBACK TRANSACTION: {str(e)}")
                    self._stats['transactions_rolled_back'] += 1
                    
                    # Log transaction rollback
                    log_database_event("database_operation", {"transaction_id": transaction_id}, {
                        "success": False,
                        "operation_type": "rollback_transaction",
                        "error": str(e),
                        "operations_count": len(transaction_context.operations)
                    }, {
                        "operation_type": "transaction_management",
                        "performance_metrics": {"execution_time_ms": 0}
                    })
                    
                except Exception as rollback_error:
                    logger = logging.getLogger(__name__)
                    logger.error(f"❌ Error during rollback: {rollback_error}")
                
                raise
            
            finally:
                # Clean up transaction context
                with self._transaction_lock:
                    self._active_transactions.pop(transaction_id, None)
                    
                    # Mark connection as not having active transaction
                    if connection_id in self._connection_info:
                        self._connection_info[connection_id].transaction_active = False
    
    def create_savepoint(self, conn: sqlite3.Connection, transaction_id: str, savepoint_name: str):
        """Create a savepoint within a transaction."""
        with self._transaction_lock:
            if transaction_id in self._active_transactions:
                conn.execute(f"SAVEPOINT {savepoint_name}")
                self._active_transactions[transaction_id].savepoints.append(savepoint_name)
                self._active_transactions[transaction_id].add_operation(f"SAVEPOINT {savepoint_name}")
    
    def rollback_to_savepoint(self, conn: sqlite3.Connection, transaction_id: str, savepoint_name: str):
        """Rollback to a specific savepoint."""
        with self._transaction_lock:
            if transaction_id in self._active_transactions:
                conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                self._active_transactions[transaction_id].add_operation(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
    
    def release_savepoint(self, conn: sqlite3.Connection, transaction_id: str, savepoint_name: str):
        """Release a savepoint."""
        with self._transaction_lock:
            if transaction_id in self._active_transactions:
                conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                transaction_context = self._active_transactions[transaction_id]
                if savepoint_name in transaction_context.savepoints:
                    transaction_context.savepoints.remove(savepoint_name)
                transaction_context.add_operation(f"RELEASE SAVEPOINT {savepoint_name}")
    
    def detect_deadlock(self, waiting_thread: int, holding_thread: int) -> bool:
        """
        Detect potential deadlocks using wait-for graph.
        
        Args:
            waiting_thread: Thread ID that is waiting
            holding_thread: Thread ID that is holding the resource
            
        Returns:
            True if deadlock detected, False otherwise
        """
        with self._deadlock_lock:
            # Add edge to wait-for graph
            if waiting_thread not in self._lock_wait_graph:
                self._lock_wait_graph[waiting_thread] = []
            
            if holding_thread not in self._lock_wait_graph[waiting_thread]:
                self._lock_wait_graph[waiting_thread].append(holding_thread)
            
            # Check for cycles (deadlock)
            visited = set()
            rec_stack = set()
            
            def has_cycle(node):
                if node in rec_stack:
                    return True
                if node in visited:
                    return False
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in self._lock_wait_graph.get(node, []):
                    if has_cycle(neighbor):
                        return True
                
                rec_stack.remove(node)
                return False
            
            # Check all nodes for cycles
            for thread_id in self._lock_wait_graph:
                if thread_id not in visited:
                    if has_cycle(thread_id):
                        self._stats['deadlocks_detected'] += 1
                        
                        # Log deadlock detection
                        log_database_event("database_operation", {
                            "waiting_thread": waiting_thread,
                            "holding_thread": holding_thread
                        }, {
                            "success": False,
                            "operation_type": "deadlock_detected",
                            "deadlock_count": self._stats['deadlocks_detected']
                        }, {
                            "operation_type": "concurrency_management",
                            "performance_metrics": {"execution_time_ms": 0}
                        })
                        
                        return True
            
            return False
    
    def clear_wait_graph_entry(self, thread_id: int):
        """Clear wait graph entry for a thread."""
        with self._deadlock_lock:
            self._lock_wait_graph.pop(thread_id, None)
            
            # Remove thread from other entries
            for waiting_thread, holding_threads in self._lock_wait_graph.items():
                if thread_id in holding_threads:
                    holding_threads.remove(thread_id)
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self._connections_lock:
            active_connections = sum(1 for info in self._connection_info.values() if info.in_use)
            active_transactions = len(self._active_transactions)
            
            return {
                "total_connections": len(self._connections),
                "active_connections": active_connections,
                "idle_connections": len(self._connections) - active_connections,
                "active_transactions": active_transactions,
                "pool_size": self._pool.qsize(),
                "max_connections": self.config.max_connections,
                "statistics": self._stats.copy(),
                "oldest_connection": min(
                    (info.created_at for info in self._connection_info.values()),
                    default=datetime.now()
                ).isoformat(),
                "newest_connection": max(
                    (info.created_at for info in self._connection_info.values()),
                    default=datetime.now()
                ).isoformat()
            }
    
    def get_active_transactions(self) -> List[Dict[str, Any]]:
        """Get information about active transactions."""
        with self._transaction_lock:
            return [
                {
                    "transaction_id": tx.transaction_id,
                    "connection_id": tx.connection_id,
                    "thread_id": tx.thread_id,
                    "started_at": tx.started_at.isoformat(),
                    "duration_seconds": (datetime.now() - tx.started_at).total_seconds(),
                    "isolation_level": tx.isolation_level.value,
                    "operations_count": len(tx.operations),
                    "savepoints_count": len(tx.savepoints)
                }
                for tx in self._active_transactions.values()
            ]
    
    def force_close_connection(self, connection_id: str) -> bool:
        """Force close a specific connection (emergency use only)."""
        with self._connections_lock:
            if connection_id in self._connections:
                try:
                    conn = self._connections[connection_id]
                    conn.close()
                    del self._connections[connection_id]
                    del self._connection_info[connection_id]
                    return True
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"❌ Error force closing connection {connection_id}: {e}")
                    return False
        return False
    
    def shutdown(self):
        """Shutdown the connection pool and cleanup resources."""
        logger = logging.getLogger(__name__)
        logger.info("🔄 Shutting down database connection pool...")
        
        # Signal cleanup thread to stop
        self._shutdown_event.set()
        
        # Wait for cleanup thread to finish
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        # Close all connections
        with self._connections_lock:
            for conn_id, conn in self._connections.items():
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"⚠️ Error closing connection {conn_id}: {e}")
            
            self._connections.clear()
            self._connection_info.clear()
        
        # Clear transaction contexts
        with self._transaction_lock:
            self._active_transactions.clear()
        
        # Clear wait graph
        with self._deadlock_lock:
            self._lock_wait_graph.clear()
        
        logger.info("✅ Database connection pool shutdown complete")


# Global connection pool instance
_connection_pool: Optional[DatabaseConnectionPool] = None
_pool_lock = threading.Lock()

def get_connection_pool() -> DatabaseConnectionPool:
    """Get the global connection pool instance."""
    global _connection_pool
    
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = DatabaseConnectionPool()
    
    return _connection_pool

def shutdown_connection_pool():
    """Shutdown the global connection pool."""
    global _connection_pool
    
    if _connection_pool is not None:
        with _pool_lock:
            if _connection_pool is not None:
                _connection_pool.shutdown()
                _connection_pool = None


# Context managers for easy use
@contextmanager
def database_connection(timeout: Optional[float] = None):
    """Get a database connection from the pool."""
    pool = get_connection_pool()
    with pool.get_connection(timeout=timeout) as conn:
        yield conn

@contextmanager
def database_transaction(isolation_level: TransactionIsolation = TransactionIsolation.READ_COMMITTED):
    """Get a transactional database connection."""
    pool = get_connection_pool()
    with pool.get_transaction(isolation_level=isolation_level) as (conn, tx_id):
        yield conn, tx_id


# Decorators for automatic transaction management
def with_database_connection(timeout: Optional[float] = None):
    """Decorator to automatically provide a database connection."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            with database_connection(timeout=timeout) as conn:
                return func(conn, *args, **kwargs)
        return wrapper
    return decorator

def with_database_transaction(isolation_level: TransactionIsolation = TransactionIsolation.READ_COMMITTED):
    """Decorator to automatically provide a transactional database connection."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            with database_transaction(isolation_level=isolation_level) as (conn, tx_id):
                return func(conn, tx_id, *args, **kwargs)
        return wrapper
    return decorator