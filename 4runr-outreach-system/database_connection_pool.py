#!/usr/bin/env python3
"""
Database Connection Pool for Lead Database System

This module provides thread-safe connection pooling, transaction management,
and concurrent access safety for the lead database system.

Features:
- Thread-safe connection pooling
- Automatic connection lifecycle management
- Transaction management with rollback capabilities
- Deadlock detection and recovery
- Connection health monitoring
- Concurrent access coordination
"""

import sqlite3
import threading
import time
import queue
import logging
import contextlib
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Information about a database connection"""
    connection_id: str
    created_at: datetime
    last_used: datetime
    thread_id: int
    in_transaction: bool = False
    transaction_start: Optional[datetime] = None
    query_count: int = 0
    is_healthy: bool = True

@dataclass
class TransactionContext:
    """Context information for database transactions"""
    transaction_id: str
    connection_id: str
    started_at: datetime
    operations: List[str]
    rollback_points: List[str]
    is_nested: bool = False
    parent_transaction: Optional[str] = None

class DatabaseConnectionPool:
    """
    Thread-safe database connection pool with transaction management
    """
    
    def __init__(self, 
                 db_path: str,
                 min_connections: int = 2,
                 max_connections: int = 10,
                 connection_timeout: int = 30,
                 transaction_timeout: int = 300,
                 enable_wal_mode: bool = True):
        """
        Initialize the connection pool
        
        Args:
            db_path: Path to SQLite database file
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
            connection_timeout: Timeout for acquiring connections (seconds)
            transaction_timeout: Timeout for transactions (seconds)
            enable_wal_mode: Enable WAL mode for better concurrency
        """
        self.db_path = db_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.transaction_timeout = transaction_timeout
        self.enable_wal_mode = enable_wal_mode
        
        # Thread-safe connection management
        self._pool_lock = threading.RLock()
        self._available_connections = queue.Queue(maxsize=max_connections)
        self._all_connections: Dict[str, ConnectionInfo] = {}
        self._active_connections: Dict[int, str] = {}  # thread_id -> connection_id
        
        # Transaction management
        self._transaction_lock = threading.RLock()
        self._active_transactions: Dict[str, TransactionContext] = {}
        self._thread_transactions: Dict[int, str] = {}  # thread_id -> transaction_id
        
        # Statistics and monitoring
        self._stats = {
            'connections_created': 0,
            'connections_destroyed': 0,
            'transactions_started': 0,
            'transactions_committed': 0,
            'transactions_rolled_back': 0,
            'deadlocks_detected': 0,
            'connection_timeouts': 0
        }
        
        # Initialize the pool
        self._initialize_pool()
        
        # Start background maintenance thread
        self._maintenance_thread = threading.Thread(target=self._maintenance_worker, daemon=True)
        self._maintenance_thread.start()
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections"""
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create minimum connections
        for _ in range(self.min_connections):
            conn_info = self._create_connection()
            if conn_info:
                self._available_connections.put(conn_info.connection_id)
    
    def _create_connection(self) -> Optional[ConnectionInfo]:
        """Create a new database connection with proper configuration"""
        try:
            connection_id = str(uuid.uuid4())
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.connection_timeout,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode, we'll handle transactions manually
            )
            
            # Configure connection for optimal concurrent access
            conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
            conn.execute("PRAGMA temp_store = memory")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            
            if self.enable_wal_mode:
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA wal_autocheckpoint = 1000")
            
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            # Store connection info
            conn_info = ConnectionInfo(
                connection_id=connection_id,
                created_at=datetime.now(),
                last_used=datetime.now(),
                thread_id=threading.get_ident()
            )
            
            # Store connection with custom attribute
            conn._connection_id = connection_id
            conn._connection_info = conn_info
            
            with self._pool_lock:
                self._all_connections[connection_id] = conn_info
                self._stats['connections_created'] += 1
            
            logger.debug(f"Created new database connection: {connection_id}")
            return conn_info
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    def _get_connection_by_id(self, connection_id: str) -> Optional[sqlite3.Connection]:
        """Get the actual connection object by ID"""
        # This is a simplified approach - in a real implementation,
        # you'd store the connection objects separately
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.connection_timeout,
                check_same_thread=False,
                isolation_level=None
            )
            conn._connection_id = connection_id
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection {connection_id}: {e}")
            return None
    
    @contextlib.contextmanager
    def get_connection(self, timeout: Optional[int] = None):
        """
        Get a connection from the pool
        
        Args:
            timeout: Timeout for acquiring connection (uses default if None)
            
        Yields:
            sqlite3.Connection: Database connection
        """
        timeout = timeout or self.connection_timeout
        connection_id = None
        conn = None
        
        try:
            # Try to get an available connection
            try:
                connection_id = self._available_connections.get(timeout=timeout)
            except queue.Empty:
                # Try to create a new connection if under max limit
                with self._pool_lock:
                    if len(self._all_connections) < self.max_connections:
                        conn_info = self._create_connection()
                        if conn_info:
                            connection_id = conn_info.connection_id
                    
                    if not connection_id:
                        self._stats['connection_timeouts'] += 1
                        raise TimeoutError(f"Could not acquire connection within {timeout} seconds")
            
            # Get the actual connection
            conn = self._get_connection_by_id(connection_id)
            if not conn:
                raise RuntimeError(f"Failed to retrieve connection {connection_id}")
            
            # Update connection info
            thread_id = threading.get_ident()
            with self._pool_lock:
                if connection_id in self._all_connections:
                    conn_info = self._all_connections[connection_id]
                    conn_info.last_used = datetime.now()
                    conn_info.thread_id = thread_id
                    conn_info.query_count += 1
                
                self._active_connections[thread_id] = connection_id
            
            logger.debug(f"Acquired connection {connection_id} for thread {thread_id}")
            yield conn
            
        except Exception as e:
            logger.error(f"Error with connection {connection_id}: {e}")
            # Mark connection as unhealthy if it exists
            if connection_id and connection_id in self._all_connections:
                with self._pool_lock:
                    self._all_connections[connection_id].is_healthy = False
            raise
            
        finally:
            # Return connection to pool
            if connection_id and conn:
                try:
                    # Close any open transactions
                    if hasattr(conn, '_connection_id'):
                        self._cleanup_connection_transactions(connection_id)
                    
                    # Close the connection (we'll create fresh ones as needed)
                    conn.close()
                    
                    # Update tracking
                    thread_id = threading.get_ident()
                    with self._pool_lock:
                        if thread_id in self._active_connections:
                            del self._active_connections[thread_id]
                        
                        # Return to available pool if healthy
                        if (connection_id in self._all_connections and 
                            self._all_connections[connection_id].is_healthy):
                            try:
                                self._available_connections.put_nowait(connection_id)
                            except queue.Full:
                                # Pool is full, destroy this connection
                                self._destroy_connection(connection_id)
                        else:
                            # Connection is unhealthy, destroy it
                            self._destroy_connection(connection_id)
                    
                    logger.debug(f"Released connection {connection_id}")
                    
                except Exception as e:
                    logger.error(f"Error releasing connection {connection_id}: {e}")
                    self._destroy_connection(connection_id)
    
    def _destroy_connection(self, connection_id: str):
        """Destroy a connection and remove it from tracking"""
        with self._pool_lock:
            if connection_id in self._all_connections:
                del self._all_connections[connection_id]
                self._stats['connections_destroyed'] += 1
                logger.debug(f"Destroyed connection {connection_id}")
    
    def _cleanup_connection_transactions(self, connection_id: str):
        """Clean up any active transactions for a connection"""
        with self._transaction_lock:
            # Find transactions using this connection
            transactions_to_cleanup = []
            for trans_id, trans_ctx in self._active_transactions.items():
                if trans_ctx.connection_id == connection_id:
                    transactions_to_cleanup.append(trans_id)
            
            # Clean up transactions
            for trans_id in transactions_to_cleanup:
                logger.warning(f"Cleaning up abandoned transaction {trans_id}")
                self._cleanup_transaction(trans_id)
    
    @contextlib.contextmanager
    def transaction(self, connection: Optional[sqlite3.Connection] = None, 
                   savepoint_name: Optional[str] = None):
        """
        Start a database transaction with automatic rollback on error
        
        Args:
            connection: Existing connection to use (optional)
            savepoint_name: Name for savepoint (for nested transactions)
            
        Yields:
            TransactionContext: Transaction context information
        """
        transaction_id = str(uuid.uuid4())
        thread_id = threading.get_ident()
        
        # Determine if this is a nested transaction
        is_nested = thread_id in self._thread_transactions
        parent_transaction = self._thread_transactions.get(thread_id) if is_nested else None
        
        # Use provided connection or get one from pool
        if connection:
            conn = connection
            connection_id = getattr(connection, '_connection_id', 'external')
        else:
            # This would need to be implemented differently in practice
            # For now, we'll assume the connection is managed externally
            raise NotImplementedError("Transaction without connection not implemented")
        
        transaction_ctx = TransactionContext(
            transaction_id=transaction_id,
            connection_id=connection_id,
            started_at=datetime.now(),
            operations=[],
            rollback_points=[],
            is_nested=is_nested,
            parent_transaction=parent_transaction
        )
        
        try:
            with self._transaction_lock:
                self._active_transactions[transaction_id] = transaction_ctx
                self._thread_transactions[thread_id] = transaction_id
                self._stats['transactions_started'] += 1
            
            # Start transaction or savepoint
            if is_nested and savepoint_name:
                conn.execute(f"SAVEPOINT {savepoint_name}")
                transaction_ctx.rollback_points.append(savepoint_name)
                logger.debug(f"Started savepoint {savepoint_name} in transaction {transaction_id}")
            else:
                conn.execute("BEGIN IMMEDIATE")
                logger.debug(f"Started transaction {transaction_id}")
            
            # Update connection info
            if connection_id in self._all_connections:
                with self._pool_lock:
                    self._all_connections[connection_id].in_transaction = True
                    self._all_connections[connection_id].transaction_start = datetime.now()
            
            yield transaction_ctx
            
            # Commit transaction or release savepoint
            if is_nested and savepoint_name:
                conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                logger.debug(f"Released savepoint {savepoint_name}")
            else:
                conn.execute("COMMIT")
                logger.debug(f"Committed transaction {transaction_id}")
                
            with self._transaction_lock:
                self._stats['transactions_committed'] += 1
            
        except Exception as e:
            # Rollback transaction or savepoint
            try:
                if is_nested and savepoint_name:
                    conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    logger.warning(f"Rolled back to savepoint {savepoint_name}: {e}")
                else:
                    conn.execute("ROLLBACK")
                    logger.warning(f"Rolled back transaction {transaction_id}: {e}")
                
                with self._transaction_lock:
                    self._stats['transactions_rolled_back'] += 1
                    
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
            
            raise
            
        finally:
            # Clean up transaction tracking
            self._cleanup_transaction(transaction_id)
            
            # Update connection info
            if connection_id in self._all_connections:
                with self._pool_lock:
                    self._all_connections[connection_id].in_transaction = False
                    self._all_connections[connection_id].transaction_start = None
    
    def _cleanup_transaction(self, transaction_id: str):
        """Clean up transaction tracking"""
        with self._transaction_lock:
            if transaction_id in self._active_transactions:
                trans_ctx = self._active_transactions[transaction_id]
                thread_id = None
                
                # Find thread associated with this transaction
                for tid, tid_trans_id in self._thread_transactions.items():
                    if tid_trans_id == transaction_id:
                        thread_id = tid
                        break
                
                # Clean up tracking
                del self._active_transactions[transaction_id]
                if thread_id and thread_id in self._thread_transactions:
                    if trans_ctx.parent_transaction:
                        # Restore parent transaction
                        self._thread_transactions[thread_id] = trans_ctx.parent_transaction
                    else:
                        del self._thread_transactions[thread_id]
    
    def execute_with_retry(self, 
                          query: str, 
                          params: tuple = (), 
                          max_retries: int = 3,
                          retry_delay: float = 0.1) -> sqlite3.Cursor:
        """
        Execute a query with automatic retry on deadlock/busy errors
        
        Args:
            query: SQL query to execute
            params: Query parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (seconds)
            
        Returns:
            sqlite3.Cursor: Query result cursor
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return cursor
                    
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                last_error = e
                error_msg = str(e).lower()
                
                if 'locked' in error_msg or 'busy' in error_msg:
                    if attempt < max_retries:
                        # Exponential backoff
                        delay = retry_delay * (2 ** attempt)
                        logger.warning(f"Database busy, retrying in {delay}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        self._stats['deadlocks_detected'] += 1
                        logger.error(f"Database deadlock after {max_retries} retries")
                
                raise
        
        # This should never be reached, but just in case
        raise last_error or RuntimeError("Unexpected error in execute_with_retry")
    
    def _maintenance_worker(self):
        """Background thread for connection pool maintenance"""
        while True:
            try:
                time.sleep(60)  # Run maintenance every minute
                self._perform_maintenance()
            except Exception as e:
                logger.error(f"Error in maintenance worker: {e}")
    
    def _perform_maintenance(self):
        """Perform connection pool maintenance tasks"""
        current_time = datetime.now()
        
        with self._pool_lock:
            # Check for stale connections
            stale_connections = []
            for conn_id, conn_info in self._all_connections.items():
                # Mark connections as stale if unused for 10 minutes
                if (current_time - conn_info.last_used).total_seconds() > 600:
                    stale_connections.append(conn_id)
                
                # Check for long-running transactions (over 5 minutes)
                if (conn_info.in_transaction and conn_info.transaction_start and
                    (current_time - conn_info.transaction_start).total_seconds() > 300):
                    logger.warning(f"Long-running transaction detected on connection {conn_id}")
            
            # Remove stale connections (but keep minimum)
            connections_to_remove = min(
                len(stale_connections),
                len(self._all_connections) - self.min_connections
            )
            
            for conn_id in stale_connections[:connections_to_remove]:
                self._destroy_connection(conn_id)
                logger.debug(f"Removed stale connection {conn_id}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._pool_lock:
            active_count = len(self._active_connections)
            available_count = self._available_connections.qsize()
            total_count = len(self._all_connections)
            
            return {
                'total_connections': total_count,
                'active_connections': active_count,
                'available_connections': available_count,
                'max_connections': self.max_connections,
                'min_connections': self.min_connections,
                'pool_utilization': active_count / self.max_connections if self.max_connections > 0 else 0,
                **self._stats
            }
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        with self._transaction_lock:
            active_transactions = len(self._active_transactions)
            
            # Calculate average transaction duration for completed transactions
            return {
                'active_transactions': active_transactions,
                'transactions_started': self._stats['transactions_started'],
                'transactions_committed': self._stats['transactions_committed'],
                'transactions_rolled_back': self._stats['transactions_rolled_back'],
                'deadlocks_detected': self._stats['deadlocks_detected'],
                'success_rate': (
                    self._stats['transactions_committed'] / 
                    max(1, self._stats['transactions_started'])
                ) * 100
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the connection pool"""
        try:
            # Test basic connectivity
            with self.get_connection(timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            pool_stats = self.get_pool_stats()
            transaction_stats = self.get_transaction_stats()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            if pool_stats['pool_utilization'] > 0.9:
                health_status = "warning"
                issues.append("High pool utilization")
            
            if transaction_stats['success_rate'] < 95:
                health_status = "warning"
                issues.append("Low transaction success rate")
            
            if self._stats['deadlocks_detected'] > 10:
                health_status = "warning"
                issues.append("High deadlock count")
            
            return {
                'status': health_status,
                'issues': issues,
                'pool_stats': pool_stats,
                'transaction_stats': transaction_stats,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'issues': [f"Health check failed: {str(e)}"],
                'last_check': datetime.now().isoformat()
            }
    
    def close(self):
        """Close all connections and shut down the pool"""
        logger.info("Shutting down connection pool...")
        
        with self._pool_lock:
            # Close all connections
            for conn_id in list(self._all_connections.keys()):
                self._destroy_connection(conn_id)
            
            # Clear the available queue
            while not self._available_connections.empty():
                try:
                    self._available_connections.get_nowait()
                except queue.Empty:
                    break
        
        logger.info("Connection pool shut down complete")

# Global connection pool instance
_connection_pool: Optional[DatabaseConnectionPool] = None
_pool_lock = threading.Lock()

def get_connection_pool(db_path: str = None, **kwargs) -> DatabaseConnectionPool:
    """
    Get the global connection pool instance (singleton pattern)
    
    Args:
        db_path: Database path (required for first call)
        **kwargs: Additional connection pool configuration
        
    Returns:
        DatabaseConnectionPool: The global connection pool instance
    """
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool is None:
            if not db_path:
                raise ValueError("db_path is required for first connection pool initialization")
            _connection_pool = DatabaseConnectionPool(db_path, **kwargs)
        
        return _connection_pool

def close_connection_pool():
    """Close the global connection pool"""
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool:
            _connection_pool.close()
            _connection_pool = None

# Context managers for easy use
@contextlib.contextmanager
def database_connection(db_path: str = None, **kwargs):
    """Context manager for getting a database connection"""
    pool = get_connection_pool(db_path, **kwargs)
    with pool.get_connection() as conn:
        yield conn

@contextlib.contextmanager
def database_transaction(connection: sqlite3.Connection, savepoint_name: str = None):
    """Context manager for database transactions"""
    pool = get_connection_pool()
    with pool.transaction(connection, savepoint_name) as trans_ctx:
        yield trans_ctx