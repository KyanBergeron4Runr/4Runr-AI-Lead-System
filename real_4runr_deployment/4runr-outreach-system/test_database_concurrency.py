#!/usr/bin/env python3
"""
Comprehensive tests for Database Concurrency and Thread Safety.

This test suite validates:
- Concurrent database operations
- Transaction management and rollback
- Connection pooling under load
- Deadlock detection and prevention
- Thread safety of all operations
- Stress testing with multiple agents
"""

import unittest
import tempfile
import shutil
import os
import threading
import time
import random
import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from database_concurrency import (
    DatabaseConnectionPool, TransactionIsolation, LockType,
    get_connection_pool, database_connection, database_transaction,
    with_database_connection, with_database_transaction
)
from database_config import DatabaseConfig
from lead_database import LeadDatabase


class TestDatabaseConcurrency(unittest.TestCase):
    """Test cases for database concurrency management."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_concurrency.db")
        
        # Create test configuration
        self.config = DatabaseConfig(
            database_path=self.db_path,
            backup_path=os.path.join(self.temp_dir, "backups"),
            max_connections=5,
            connection_timeout=10
        )
        
        # Create connection pool
        self.pool = DatabaseConnectionPool(self.config)
        
        # Initialize database schema
        with self.pool.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    value TEXT,
                    thread_id INTEGER,
                    timestamp REAL
                )
            """)
            conn.commit()
    
    def tearDown(self):
        """Clean up test environment."""
        self.pool.shutdown()
        shutil.rmtree(self.temp_dir)
    
    def test_connection_pool_basic_operations(self):
        """Test basic connection pool operations."""
        # Test getting and returning connections
        connections = []
        
        # Get multiple connections
        for i in range(3):
            conn_context = self.pool.get_connection()
            conn = conn_context.__enter__()
            connections.append((conn_context, conn))
            
            # Test connection works
            result = conn.execute("SELECT 1").fetchone()
            self.assertEqual(result[0], 1)
        
        # Return connections
        for conn_context, conn in connections:
            conn_context.__exit__(None, None, None)
        
        # Verify pool statistics
        stats = self.pool.get_pool_statistics()
        self.assertGreaterEqual(stats['total_connections'], 3)
        self.assertEqual(stats['active_connections'], 0)
    
    def test_connection_pool_max_connections(self):
        """Test connection pool respects max connections limit."""
        connections = []
        
        try:
            # Get all available connections
            for i in range(self.config.max_connections):
                conn_context = self.pool.get_connection()
                conn = conn_context.__enter__()
                connections.append((conn_context, conn))
            
            # Try to get one more connection (should timeout)
            start_time = time.time()
            try:
                with self.pool.get_connection(timeout=1) as conn:
                    self.fail("Should have timed out")
            except Exception:
                # Expected timeout
                elapsed = time.time() - start_time
                self.assertGreaterEqual(elapsed, 0.9)  # Should have waited close to 1 second
        
        finally:
            # Return all connections
            for conn_context, conn in connections:
                conn_context.__exit__(None, None, None)
    
    def test_transaction_management(self):
        """Test transaction management with commit and rollback."""
        # Test successful transaction
        with self.pool.get_transaction() as (conn, tx_id):
            conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                        ("test_commit", threading.get_ident()))
            
            # Verify data exists within transaction
            result = conn.execute("SELECT COUNT(*) FROM test_table WHERE value = ?", 
                                ("test_commit",)).fetchone()
            self.assertEqual(result[0], 1)
        
        # Verify data was committed
        with self.pool.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table WHERE value = ?", 
                                ("test_commit",)).fetchone()
            self.assertEqual(result[0], 1)
        
        # Test rollback transaction
        try:
            with self.pool.get_transaction() as (conn, tx_id):
                conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                            ("test_rollback", threading.get_ident()))
                
                # Verify data exists within transaction
                result = conn.execute("SELECT COUNT(*) FROM test_table WHERE value = ?", 
                                    ("test_rollback",)).fetchone()
                self.assertEqual(result[0], 1)
                
                # Force rollback by raising exception
                raise ValueError("Test rollback")
        
        except ValueError:
            pass  # Expected exception
        
        # Verify data was rolled back
        with self.pool.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table WHERE value = ?", 
                                ("test_rollback",)).fetchone()
            self.assertEqual(result[0], 0)
    
    def test_savepoints(self):
        """Test savepoint functionality within transactions."""
        with self.pool.get_transaction() as (conn, tx_id):
            # Insert initial data
            conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                        ("initial", threading.get_ident()))
            
            # Create savepoint
            self.pool.create_savepoint(conn, tx_id, "sp1")
            
            # Insert more data
            conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                        ("after_savepoint", threading.get_ident()))
            
            # Verify both records exist
            result = conn.execute("SELECT COUNT(*) FROM test_table WHERE thread_id = ?", 
                                (threading.get_ident(),)).fetchone()
            self.assertEqual(result[0], 2)
            
            # Rollback to savepoint
            self.pool.rollback_to_savepoint(conn, tx_id, "sp1")
            
            # Verify only initial record exists
            result = conn.execute("SELECT COUNT(*) FROM test_table WHERE thread_id = ?", 
                                (threading.get_ident(),)).fetchone()
            self.assertEqual(result[0], 1)
            
            result = conn.execute("SELECT value FROM test_table WHERE thread_id = ?", 
                                (threading.get_ident(),)).fetchone()
            self.assertEqual(result[0], "initial")
    
    def test_concurrent_reads(self):
        """Test concurrent read operations."""
        # Insert test data
        with self.pool.get_connection() as conn:
            for i in range(100):
                conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                            (f"read_test_{i}", 0))
            conn.commit()
        
        def read_worker(worker_id):
            """Worker function for concurrent reads."""
            results = []
            with self.pool.get_connection() as conn:
                for i in range(10):
                    result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
                    results.append(result[0])
                    time.sleep(0.01)  # Small delay
            return results
        
        # Run concurrent reads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(read_worker, i) for i in range(5)]
            
            all_results = []
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        # Verify all reads returned consistent results
        expected_count = 100
        for count in all_results:
            self.assertEqual(count, expected_count)
    
    def test_concurrent_writes(self):
        """Test concurrent write operations."""
        def write_worker(worker_id):
            """Worker function for concurrent writes."""
            results = []
            for i in range(10):
                try:
                    with self.pool.get_transaction() as (conn, tx_id):
                        conn.execute("INSERT INTO test_table (value, thread_id, timestamp) VALUES (?, ?, ?)", 
                                   (f"worker_{worker_id}_item_{i}", threading.get_ident(), time.time()))
                        results.append("success")
                except Exception as e:
                    results.append(f"error: {str(e)}")
            return results
        
        # Run concurrent writes
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_worker, i) for i in range(5)]
            
            all_results = []
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        # Verify most writes succeeded
        success_count = sum(1 for result in all_results if result == "success")
        self.assertGreater(success_count, 40)  # At least 80% success rate
        
        # Verify data was written
        with self.pool.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            self.assertEqual(result[0], success_count)
    
    def test_concurrent_read_write(self):
        """Test mixed concurrent read and write operations."""
        # Insert initial data
        with self.pool.get_connection() as conn:
            for i in range(50):
                conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                            (f"initial_{i}", 0))
            conn.commit()
        
        def read_worker():
            """Worker function for reads."""
            counts = []
            for i in range(20):
                with self.pool.get_connection() as conn:
                    result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
                    counts.append(result[0])
                time.sleep(0.01)
            return counts
        
        def write_worker(worker_id):
            """Worker function for writes."""
            for i in range(10):
                try:
                    with self.pool.get_transaction() as (conn, tx_id):
                        conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                                   (f"concurrent_{worker_id}_{i}", threading.get_ident()))
                except Exception:
                    pass  # Ignore errors for this test
                time.sleep(0.02)
        
        # Run mixed operations
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Start read workers
            read_futures = [executor.submit(read_worker) for _ in range(3)]
            
            # Start write workers
            write_futures = [executor.submit(write_worker, i) for i in range(3)]
            
            # Wait for all to complete
            for future in as_completed(read_futures + write_futures):
                future.result()
        
        # Verify final state
        with self.pool.get_connection() as conn:
            final_count = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()[0]
            self.assertGreaterEqual(final_count, 50)  # At least initial data
    
    def test_deadlock_detection(self):
        """Test deadlock detection mechanism."""
        # This is a simplified test since creating actual deadlocks is complex
        thread1_id = 12345
        thread2_id = 67890
        
        # Simulate wait-for graph that would create a cycle
        self.assertFalse(self.pool.detect_deadlock(thread1_id, thread2_id))
        self.assertTrue(self.pool.detect_deadlock(thread2_id, thread1_id))  # Creates cycle
        
        # Clear wait graph
        self.pool.clear_wait_graph_entry(thread1_id)
        self.pool.clear_wait_graph_entry(thread2_id)
    
    def test_connection_cleanup(self):
        """Test connection cleanup functionality."""
        initial_stats = self.pool.get_pool_statistics()
        
        # Create and use connections
        for i in range(3):
            with self.pool.get_connection() as conn:
                conn.execute("SELECT 1")
        
        # Verify connections were created and returned
        stats = self.pool.get_pool_statistics()
        self.assertGreaterEqual(stats['total_connections'], initial_stats['total_connections'])
        self.assertEqual(stats['active_connections'], 0)
    
    def test_transaction_isolation(self):
        """Test transaction isolation levels."""
        # Insert initial data
        with self.pool.get_connection() as conn:
            conn.execute("INSERT INTO test_table (value, thread_id) VALUES (?, ?)", 
                        ("isolation_test", 0))
            conn.commit()
        
        def transaction_worker(isolation_level, worker_id):
            """Worker that performs operations with specific isolation level."""
            results = []
            try:
                with self.pool.get_transaction(isolation_level=isolation_level) as (conn, tx_id):
                    # Read initial state
                    result = conn.execute("SELECT COUNT(*) FROM test_table WHERE value = ?", 
                                        ("isolation_test",)).fetchone()
                    results.append(f"initial_count: {result[0]}")
                    
                    # Modify data
                    conn.execute("UPDATE test_table SET value = ? WHERE value = ?", 
                               (f"modified_by_{worker_id}", "isolation_test"))
                    
                    # Read modified state
                    result = conn.execute("SELECT COUNT(*) FROM test_table WHERE value = ?", 
                                        (f"modified_by_{worker_id}",)).fetchone()
                    results.append(f"modified_count: {result[0]}")
                    
                    time.sleep(0.1)  # Hold transaction open
                    
            except Exception as e:
                results.append(f"error: {str(e)}")
            
            return results
        
        # Test with READ_COMMITTED isolation
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(transaction_worker, TransactionIsolation.READ_COMMITTED, 1)
            future2 = executor.submit(transaction_worker, TransactionIsolation.READ_COMMITTED, 2)
            
            results1 = future1.result()
            results2 = future2.result()
            
            # Both should see initial data and be able to modify
            self.assertIn("initial_count: 1", results1)
            self.assertIn("initial_count: 1", results2)
    
    def test_stress_concurrent_operations(self):
        """Stress test with many concurrent operations."""
        def stress_worker(worker_id):
            """Worker that performs various database operations."""
            operations = []
            
            for i in range(20):
                operation_type = random.choice(['read', 'write', 'transaction'])
                
                try:
                    if operation_type == 'read':
                        with self.pool.get_connection() as conn:
                            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
                            operations.append(f"read: {result[0]}")
                    
                    elif operation_type == 'write':
                        with self.pool.get_connection() as conn:
                            conn.execute("INSERT INTO test_table (value, thread_id, timestamp) VALUES (?, ?, ?)", 
                                       (f"stress_{worker_id}_{i}", threading.get_ident(), time.time()))
                            conn.commit()
                            operations.append("write: success")
                    
                    elif operation_type == 'transaction':
                        with self.pool.get_transaction() as (conn, tx_id):
                            conn.execute("INSERT INTO test_table (value, thread_id, timestamp) VALUES (?, ?, ?)", 
                                       (f"tx_stress_{worker_id}_{i}", threading.get_ident(), time.time()))
                            
                            # Random chance of rollback
                            if random.random() < 0.1:  # 10% chance
                                raise ValueError("Random rollback")
                            
                            operations.append("transaction: success")
                
                except Exception as e:
                    operations.append(f"error: {str(e)}")
                
                # Random delay
                time.sleep(random.uniform(0.001, 0.01))
            
            return operations
        
        # Run stress test with many workers
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(10)]
            
            all_operations = []
            for future in as_completed(futures):
                operations = future.result()
                all_operations.extend(operations)
        
        end_time = time.time()
        
        # Verify stress test completed in reasonable time
        self.assertLess(end_time - start_time, 30)  # Should complete within 30 seconds
        
        # Verify operations were performed
        self.assertGreater(len(all_operations), 100)
        
        # Verify database is still functional
        with self.pool.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            self.assertGreater(result[0], 0)
    
    def test_pool_statistics(self):
        """Test connection pool statistics."""
        stats = self.pool.get_pool_statistics()
        
        # Verify statistics structure
        required_keys = [
            'total_connections', 'active_connections', 'idle_connections',
            'active_transactions', 'pool_size', 'max_connections', 'statistics'
        ]
        
        for key in required_keys:
            self.assertIn(key, stats)
        
        # Verify statistics make sense
        self.assertGreaterEqual(stats['total_connections'], 0)
        self.assertGreaterEqual(stats['active_connections'], 0)
        self.assertGreaterEqual(stats['idle_connections'], 0)
        self.assertEqual(stats['max_connections'], self.config.max_connections)
        
        # Test with active connections
        with self.pool.get_connection() as conn:
            active_stats = self.pool.get_pool_statistics()
            self.assertGreater(active_stats['active_connections'], stats['active_connections'])
    
    def test_active_transactions_tracking(self):
        """Test tracking of active transactions."""
        # Initially no active transactions
        active_txs = self.pool.get_active_transactions()
        self.assertEqual(len(active_txs), 0)
        
        # Start a transaction
        with self.pool.get_transaction() as (conn, tx_id):
            active_txs = self.pool.get_active_transactions()
            self.assertEqual(len(active_txs), 1)
            
            tx_info = active_txs[0]
            self.assertEqual(tx_info['transaction_id'], tx_id)
            self.assertIn('started_at', tx_info)
            self.assertIn('duration_seconds', tx_info)
            self.assertIn('operations_count', tx_info)
        
        # Transaction should be cleaned up
        active_txs = self.pool.get_active_transactions()
        self.assertEqual(len(active_txs), 0)


class TestDatabaseConcurrencyIntegration(unittest.TestCase):
    """Integration tests for database concurrency with LeadDatabase."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")
        
        # Create test database
        self.db = LeadDatabase(self.db_path)
        
        # Sample lead data
        self.sample_leads = [
            {
                "full_name": f"Concurrent Test {i}",
                "company": f"Concurrent Corp {i}",
                "email": f"test{i}@concurrent.com",
                "source": "concurrency_test"
            }
            for i in range(50)
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_concurrent_lead_operations(self):
        """Test concurrent lead database operations."""
        def lead_worker(worker_id, leads_subset):
            """Worker that performs lead operations."""
            results = []
            
            for lead_data in leads_subset:
                try:
                    # Add lead
                    lead_id = self.db.add_lead(lead_data)
                    results.append(f"added: {lead_id}")
                    
                    # Get lead
                    retrieved_lead = self.db.get_lead(lead_id)
                    if retrieved_lead:
                        results.append("retrieved: success")
                    
                    # Update lead
                    update_success = self.db.update_lead(lead_id, {"title": f"Updated by worker {worker_id}"})
                    if update_success:
                        results.append("updated: success")
                
                except Exception as e:
                    results.append(f"error: {str(e)}")
            
            return results
        
        # Divide leads among workers
        chunk_size = len(self.sample_leads) // 5
        lead_chunks = [
            self.sample_leads[i:i + chunk_size] 
            for i in range(0, len(self.sample_leads), chunk_size)
        ]
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(lead_worker, i, chunk) 
                for i, chunk in enumerate(lead_chunks)
            ]
            
            all_results = []
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        # Verify operations succeeded
        success_count = sum(1 for result in all_results if "success" in result or "added:" in result)
        self.assertGreater(success_count, len(self.sample_leads))  # At least one success per lead
        
        # Verify final database state
        stats = self.db.get_database_stats()
        self.assertGreater(stats['total_leads'], 0)
    
    def test_concurrent_search_operations(self):
        """Test concurrent search operations."""
        # Add test data
        for lead_data in self.sample_leads[:10]:
            self.db.add_lead(lead_data)
        
        def search_worker(worker_id):
            """Worker that performs search operations."""
            results = []
            
            for i in range(10):
                try:
                    # Search by company
                    search_results = self.db.search_leads({"company": f"Concurrent Corp {i % 5}"})
                    results.append(f"search: {len(search_results)} results")
                    
                    # Get all leads
                    all_leads = self.db.search_leads({})
                    results.append(f"all: {len(all_leads)} leads")
                
                except Exception as e:
                    results.append(f"error: {str(e)}")
            
            return results
        
        # Run concurrent searches
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_worker, i) for i in range(5)]
            
            all_results = []
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        # Verify searches completed successfully
        error_count = sum(1 for result in all_results if "error:" in result)
        self.assertLess(error_count, len(all_results) * 0.1)  # Less than 10% errors


class TestConcurrencyDecorators(unittest.TestCase):
    """Test concurrency decorators and context managers."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_decorators.db")
        
        # Create test configuration
        self.config = DatabaseConfig(
            database_path=self.db_path,
            backup_path=os.path.join(self.temp_dir, "backups"),
            max_connections=3
        )
        
        # Initialize database
        with database_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decorator_test (
                    id INTEGER PRIMARY KEY,
                    value TEXT,
                    created_at REAL
                )
            """)
            conn.commit()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_database_connection_context_manager(self):
        """Test database_connection context manager."""
        with database_connection() as conn:
            result = conn.execute("SELECT 1").fetchone()
            self.assertEqual(result[0], 1)
    
    def test_database_transaction_context_manager(self):
        """Test database_transaction context manager."""
        # Test successful transaction
        with database_transaction() as (conn, tx_id):
            conn.execute("INSERT INTO decorator_test (value, created_at) VALUES (?, ?)", 
                        ("test_commit", time.time()))
            
            # Verify data exists within transaction
            result = conn.execute("SELECT COUNT(*) FROM decorator_test WHERE value = ?", 
                                ("test_commit",)).fetchone()
            self.assertEqual(result[0], 1)
        
        # Verify data was committed
        with database_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM decorator_test WHERE value = ?", 
                                ("test_commit",)).fetchone()
            self.assertEqual(result[0], 1)
    
    def test_with_database_connection_decorator(self):
        """Test with_database_connection decorator."""
        @with_database_connection()
        def test_function(conn, test_value):
            conn.execute("INSERT INTO decorator_test (value, created_at) VALUES (?, ?)", 
                        (test_value, time.time()))
            conn.commit()
            
            result = conn.execute("SELECT COUNT(*) FROM decorator_test WHERE value = ?", 
                                (test_value,)).fetchone()
            return result[0]
        
        count = test_function("decorator_test")
        self.assertEqual(count, 1)
    
    def test_with_database_transaction_decorator(self):
        """Test with_database_transaction decorator."""
        @with_database_transaction()
        def test_function(conn, tx_id, test_value):
            conn.execute("INSERT INTO decorator_test (value, created_at) VALUES (?, ?)", 
                        (test_value, time.time()))
            
            result = conn.execute("SELECT COUNT(*) FROM decorator_test WHERE value = ?", 
                                (test_value,)).fetchone()
            return result[0], tx_id
        
        count, tx_id = test_function("transaction_decorator_test")
        self.assertEqual(count, 1)
        self.assertIsNotNone(tx_id)
        
        # Verify data was committed
        with database_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM decorator_test WHERE value = ?", 
                                ("transaction_decorator_test",)).fetchone()
            self.assertEqual(result[0], 1)


if __name__ == '__main__':
    # Run the concurrency tests
    unittest.main(verbosity=2)