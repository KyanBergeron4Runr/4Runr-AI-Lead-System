#!/usr/bin/env python3
"""
Thread Safety Tests for Lead Database System

This module contains comprehensive tests for thread safety and concurrent
operations in the lead database system.

Test Categories:
- Thread-safe database operations
- Connection pool thread safety
- Transaction isolation
- Data consistency under concurrent access
- Race condition detection
- Memory consistency tests
"""

import unittest
import threading
import time
import random
import sqlite3
import tempfile
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Set
import uuid
from datetime import datetime
import queue
import weakref
import gc

# Import our modules
from lead_database import LeadDatabase
from database_connection_pool import DatabaseConnectionPool, get_connection_pool, close_connection_pool
from concurrent_access_manager import ConcurrentAccessManager, OperationPriority, LockType

class ThreadSafetyTests(unittest.TestCase):
    """Comprehensive thread safety tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "thread_safety_test.db")
        
        # Initialize components
        self.lead_db = LeadDatabase(self.db_path)
        self.access_manager = ConcurrentAccessManager(
            db_path=self.db_path,
            max_concurrent_operations=20,
            deadlock_detection_interval=1
        )
        
        # Thread safety tracking
        self.thread_results = {}
        self.thread_errors = {}
        self.race_conditions = []
        self.data_inconsistencies = []
        
        # Synchronization primitives for tests
        self.barrier = None
        self.start_event = threading.Event()
        self.results_lock = threading.Lock()
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            self.access_manager.shutdown()
            close_connection_pool()
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def _record_thread_result(self, thread_id: int, operation: str, result: Any, error: Exception = None):
        """Thread-safe result recording"""
        with self.results_lock:
            if thread_id not in self.thread_results:
                self.thread_results[thread_id] = []
            
            self.thread_results[thread_id].append({
                'operation': operation,
                'result': result,
                'timestamp': time.time(),
                'thread_id': thread_id
            })
            
            if error:
                if thread_id not in self.thread_errors:
                    self.thread_errors[thread_id] = []
                self.thread_errors[thread_id].append({
                    'operation': operation,
                    'error': str(error),
                    'timestamp': time.time()
                })
    
    def test_concurrent_database_initialization(self):
        """Test thread safety of database initialization"""
        print("\n=== Testing Concurrent Database Initialization ===")
        
        num_threads = 10
        init_results = {}
        init_lock = threading.Lock()
        
        def init_database(thread_id: int):
            """Initialize database from multiple threads"""
            try:
                # Create a new database instance
                db_path = os.path.join(self.test_dir, f"init_test_{thread_id}.db")
                db = LeadDatabase(db_path)
                
                # Verify database is properly initialized
                stats = db.get_database_stats()
                
                with init_lock:
                    init_results[thread_id] = {
                        'success': True,
                        'stats': stats,
                        'db_path': db_path
                    }
                
                self._record_thread_result(thread_id, 'init_database', True)
                
            except Exception as e:
                with init_lock:
                    init_results[thread_id] = {
                        'success': False,
                        'error': str(e)
                    }
                self._record_thread_result(thread_id, 'init_database', False, e)
        
        # Start threads simultaneously
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=init_database,
                args=(thread_id,),
                name=f"InitThread-{thread_id}"
            )
            threads.append(thread)
        
        # Start all threads at once
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify results
        successful_inits = sum(1 for result in init_results.values() if result['success'])
        
        print(f"Successful initializations: {successful_inits}/{num_threads}")
        
        # All initializations should succeed
        self.assertEqual(successful_inits, num_threads)
        
        # Verify each database is properly set up
        for thread_id, result in init_results.items():
            if result['success']:
                self.assertIn('total_leads', result['stats'])
                self.assertTrue(os.path.exists(result['db_path']))
    
    def test_concurrent_lead_insertion_race_conditions(self):
        """Test for race conditions in concurrent lead insertion"""
        print("\n=== Testing Concurrent Lead Insertion Race Conditions ===")
        
        num_threads = 20
        leads_per_thread = 50
        
        # Use barrier to ensure all threads start simultaneously
        self.barrier = threading.Barrier(num_threads)
        
        # Shared data to detect race conditions
        insertion_order = []
        order_lock = threading.Lock()
        
        def insert_leads_with_timing(thread_id: int):
            """Insert leads and track timing for race condition detection"""
            try:
                # Wait for all threads to be ready
                self.barrier.wait()
                
                for i in range(leads_per_thread):
                    start_time = time.time()
                    
                    # Create lead with unique identifier
                    lead = {
                        'full_name': f'Race Test User T{thread_id}I{i}',
                        'email': f'race_t{thread_id}i{i}@test.com',
                        'company': f'Race Test Corp {thread_id}',
                        'linkedin_url': f'https://linkedin.com/in/race-t{thread_id}i{i}',
                        'source': 'race_condition_test'
                    }
                    
                    # Insert lead
                    lead_id = self.lead_db.add_lead(lead)
                    
                    end_time = time.time()
                    
                    # Record insertion order and timing
                    with order_lock:
                        insertion_order.append({
                            'thread_id': thread_id,
                            'iteration': i,
                            'lead_id': lead_id,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': end_time - start_time
                        })
                    
                    self._record_thread_result(thread_id, 'insert_lead', lead_id)
                    
                    # Small random delay to increase chance of race conditions
                    time.sleep(random.uniform(0.001, 0.005))
                
            except Exception as e:
                self._record_thread_result(thread_id, 'insert_lead', None, e)
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=insert_leads_with_timing,
                args=(thread_id,),
                name=f"RaceThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=120)
        
        end_time = time.time()
        
        # Analyze results for race conditions
        total_insertions = len(insertion_order)
        expected_insertions = num_threads * leads_per_thread
        
        print(f"Total insertions: {total_insertions}/{expected_insertions}")
        print(f"Test duration: {end_time - start_time:.2f} seconds")
        
        # Check for data consistency
        db_stats = self.lead_db.get_database_stats()
        print(f"Database reports {db_stats['total_leads']} leads")
        
        # Verify no duplicate lead IDs
        lead_ids = [entry['lead_id'] for entry in insertion_order if entry['lead_id']]
        unique_lead_ids = set(lead_ids)
        
        if len(lead_ids) != len(unique_lead_ids):
            duplicate_count = len(lead_ids) - len(unique_lead_ids)
            self.race_conditions.append(f"Found {duplicate_count} duplicate lead IDs")
            print(f"WARNING: Found {duplicate_count} duplicate lead IDs")
        
        # Check for timing anomalies that might indicate race conditions
        durations = [entry['duration'] for entry in insertion_order]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Flag unusually long operations (potential deadlocks/contention)
        long_operations = [d for d in durations if d > avg_duration * 10]
        if long_operations:
            print(f"WARNING: Found {len(long_operations)} unusually long operations")
            print(f"Average duration: {avg_duration:.3f}s, Max duration: {max_duration:.3f}s")
        
        # Verify database integrity
        self._verify_database_integrity()
        
        # Assertions
        self.assertEqual(total_insertions, expected_insertions)
        self.assertEqual(len(lead_ids), len(unique_lead_ids), "Duplicate lead IDs detected")
    
    def test_connection_pool_thread_safety(self):
        """Test thread safety of connection pool operations"""
        print("\n=== Testing Connection Pool Thread Safety ===")
        
        num_threads = 50
        connections_per_thread = 20
        
        # Track connection usage
        connection_usage = {}
        usage_lock = threading.Lock()
        
        def connection_worker(thread_id: int):
            """Worker that acquires and releases connections"""
            try:
                thread_connections = []
                
                for i in range(connections_per_thread):
                    # Acquire connection
                    with self.access_manager.connection_pool.get_connection(timeout=10) as conn:
                        conn_id = getattr(conn, '_connection_id', f'unknown_{thread_id}_{i}')
                        thread_connections.append(conn_id)
                        
                        # Record connection usage
                        with usage_lock:
                            if conn_id not in connection_usage:
                                connection_usage[conn_id] = []
                            connection_usage[conn_id].append({
                                'thread_id': thread_id,
                                'iteration': i,
                                'acquired_at': time.time()
                            })
                        
                        # Perform a simple operation
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM leads")
                        result = cursor.fetchone()
                        
                        # Hold connection for a short time
                        time.sleep(random.uniform(0.001, 0.01))
                
                self._record_thread_result(thread_id, 'connection_operations', len(thread_connections))
                
            except Exception as e:
                self._record_thread_result(thread_id, 'connection_operations', 0, e)
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=connection_worker,
                args=(thread_id,),
                name=f"ConnThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)
        
        end_time = time.time()
        
        # Analyze connection usage
        total_acquisitions = sum(len(usage) for usage in connection_usage.values())
        unique_connections = len(connection_usage)
        
        print(f"Total connection acquisitions: {total_acquisitions}")
        print(f"Unique connections used: {unique_connections}")
        print(f"Test duration: {end_time - start_time:.2f} seconds")
        
        # Check for connection reuse (good for pool efficiency)
        reused_connections = sum(1 for usage in connection_usage.values() if len(usage) > 1)
        print(f"Connections reused: {reused_connections}/{unique_connections}")
        
        # Verify pool health after stress test
        pool_health = self.access_manager.connection_pool.health_check()
        print(f"Pool health after test: {pool_health['status']}")
        
        # Check for thread safety violations
        for conn_id, usage_list in connection_usage.items():
            # Sort by acquisition time
            usage_list.sort(key=lambda x: x['acquired_at'])
            
            # Check for overlapping usage (would indicate thread safety violation)
            for i in range(len(usage_list) - 1):
                current = usage_list[i]
                next_usage = usage_list[i + 1]
                
                # If acquisitions are too close, might indicate concurrent access
                time_diff = next_usage['acquired_at'] - current['acquired_at']
                if time_diff < 0.001:  # Less than 1ms apart
                    self.race_conditions.append(
                        f"Potential concurrent access to connection {conn_id} "
                        f"by threads {current['thread_id']} and {next_usage['thread_id']}"
                    )
        
        # Assertions
        self.assertEqual(pool_health['status'], 'healthy')
        self.assertGreater(total_acquisitions, 0)
        self.assertEqual(len(self.race_conditions), 0, f"Race conditions detected: {self.race_conditions}")
    
    def test_transaction_isolation(self):
        """Test transaction isolation between concurrent threads"""
        print("\n=== Testing Transaction Isolation ===")
        
        num_threads = 10
        transactions_per_thread = 5
        
        # Shared counter to test isolation
        shared_counter = {'value': 0}
        counter_lock = threading.Lock()
        
        def transaction_worker(thread_id: int):
            """Worker that performs transactions with shared data"""
            try:
                for i in range(transactions_per_thread):
                    def transaction_operation():
                        with self.access_manager.connection_pool.get_connection() as conn:
                            # Start transaction
                            conn.execute("BEGIN IMMEDIATE")
                            
                            try:
                                # Read current counter value from database
                                cursor = conn.cursor()
                                cursor.execute("SELECT COUNT(*) as count FROM leads WHERE source = 'isolation_test'")
                                current_count = cursor.fetchone()['count']
                                
                                # Simulate some processing time
                                time.sleep(random.uniform(0.01, 0.05))
                                
                                # Insert a new lead (incrementing counter)
                                lead = {
                                    'full_name': f'Isolation Test T{thread_id}I{i}',
                                    'email': f'isolation_t{thread_id}i{i}@test.com',
                                    'company': f'Isolation Corp {thread_id}',
                                    'source': 'isolation_test'
                                }
                                
                                cursor.execute("""
                                    INSERT INTO leads (id, full_name, email, company, source, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    str(uuid.uuid4()),
                                    lead['full_name'],
                                    lead['email'],
                                    lead['company'],
                                    lead['source'],
                                    datetime.now().isoformat()
                                ))
                                
                                # Verify the count increased by exactly 1
                                cursor.execute("SELECT COUNT(*) as count FROM leads WHERE source = 'isolation_test'")
                                new_count = cursor.fetchone()['count']
                                
                                expected_count = current_count + 1
                                if new_count != expected_count:
                                    self.data_inconsistencies.append(
                                        f"Thread {thread_id} iteration {i}: "
                                        f"Expected count {expected_count}, got {new_count}"
                                    )
                                
                                # Commit transaction
                                conn.execute("COMMIT")
                                
                                # Update shared counter for verification
                                with counter_lock:
                                    shared_counter['value'] += 1
                                
                                return True
                                
                            except Exception as e:
                                conn.execute("ROLLBACK")
                                raise
                    
                    result = self.access_manager.execute_operation(
                        operation_type="isolation_test",
                        callback=transaction_operation,
                        priority=OperationPriority.NORMAL,
                        timeout=30
                    )
                    
                    self._record_thread_result(thread_id, 'transaction', result)
                
            except Exception as e:
                self._record_thread_result(thread_id, 'transaction', False, e)
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=transaction_worker,
                args=(thread_id,),
                name=f"TransThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=120)
        
        end_time = time.time()
        
        # Verify isolation
        expected_total = num_threads * transactions_per_thread
        actual_shared_counter = shared_counter['value']
        
        # Check database count
        with self.lead_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM leads WHERE source = 'isolation_test'")
            db_count = cursor.fetchone()['count']
        
        print(f"Expected transactions: {expected_total}")
        print(f"Shared counter value: {actual_shared_counter}")
        print(f"Database count: {db_count}")
        print(f"Data inconsistencies found: {len(self.data_inconsistencies)}")
        print(f"Test duration: {end_time - start_time:.2f} seconds")
        
        if self.data_inconsistencies:
            print("Data inconsistencies:")
            for inconsistency in self.data_inconsistencies[:5]:  # Show first 5
                print(f"  - {inconsistency}")
        
        # Assertions
        self.assertEqual(actual_shared_counter, db_count, "Shared counter and database count mismatch")
        self.assertEqual(len(self.data_inconsistencies), 0, "Transaction isolation violations detected")
    
    def test_memory_consistency(self):
        """Test memory consistency across threads"""
        print("\n=== Testing Memory Consistency ===")
        
        num_threads = 20
        operations_per_thread = 100
        
        # Shared data structures to test memory consistency
        shared_data = {
            'lead_ids': set(),
            'operation_count': 0,
            'last_operation_time': 0
        }
        data_lock = threading.Lock()
        
        def memory_consistency_worker(thread_id: int):
            """Worker that tests memory consistency"""
            try:
                local_lead_ids = set()
                
                for i in range(operations_per_thread):
                    # Create and insert lead
                    lead = {
                        'full_name': f'Memory Test T{thread_id}I{i}',
                        'email': f'memory_t{thread_id}i{i}@test.com',
                        'company': f'Memory Corp {thread_id}',
                        'source': 'memory_consistency_test'
                    }
                    
                    lead_id = self.lead_db.add_lead(lead)
                    local_lead_ids.add(lead_id)
                    
                    # Update shared data with proper synchronization
                    current_time = time.time()
                    with data_lock:
                        shared_data['lead_ids'].add(lead_id)
                        shared_data['operation_count'] += 1
                        shared_data['last_operation_time'] = current_time
                    
                    # Verify memory consistency
                    with data_lock:
                        # Check that our lead_id is in the shared set
                        if lead_id not in shared_data['lead_ids']:
                            self.data_inconsistencies.append(
                                f"Thread {thread_id}: Lead ID {lead_id} not found in shared data"
                            )
                        
                        # Check operation count consistency
                        expected_min_count = len(local_lead_ids)
                        if shared_data['operation_count'] < expected_min_count:
                            self.data_inconsistencies.append(
                                f"Thread {thread_id}: Operation count inconsistency"
                            )
                    
                    # Small delay to increase chance of memory consistency issues
                    time.sleep(random.uniform(0.001, 0.003))
                
                self._record_thread_result(thread_id, 'memory_consistency', len(local_lead_ids))
                
            except Exception as e:
                self._record_thread_result(thread_id, 'memory_consistency', 0, e)
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=memory_consistency_worker,
                args=(thread_id,),
                name=f"MemThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=120)
        
        end_time = time.time()
        
        # Verify memory consistency
        expected_operations = num_threads * operations_per_thread
        actual_operations = shared_data['operation_count']
        unique_lead_ids = len(shared_data['lead_ids'])
        
        print(f"Expected operations: {expected_operations}")
        print(f"Actual operations: {actual_operations}")
        print(f"Unique lead IDs: {unique_lead_ids}")
        print(f"Memory inconsistencies: {len(self.data_inconsistencies)}")
        print(f"Test duration: {end_time - start_time:.2f} seconds")
        
        if self.data_inconsistencies:
            print("Memory inconsistencies:")
            for inconsistency in self.data_inconsistencies[:5]:
                print(f"  - {inconsistency}")
        
        # Verify database consistency
        with self.lead_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM leads WHERE source = 'memory_consistency_test'")
            db_count = cursor.fetchone()['count']
        
        print(f"Database count: {db_count}")
        
        # Assertions
        self.assertEqual(actual_operations, expected_operations)
        self.assertEqual(unique_lead_ids, expected_operations)
        self.assertEqual(db_count, expected_operations)
        self.assertEqual(len(self.data_inconsistencies), 0, "Memory consistency violations detected")
    
    def test_resource_cleanup_thread_safety(self):
        """Test thread safety of resource cleanup"""
        print("\n=== Testing Resource Cleanup Thread Safety ===")
        
        num_threads = 15
        resources_per_thread = 20
        
        # Track resource lifecycle
        resource_lifecycle = {}
        lifecycle_lock = threading.Lock()
        
        def resource_worker(thread_id: int):
            """Worker that creates and cleans up resources"""
            try:
                thread_resources = []
                
                for i in range(resources_per_thread):
                    # Create a "resource" (database connection + operation)
                    resource_id = f"resource_t{thread_id}i{i}"
                    
                    with lifecycle_lock:
                        resource_lifecycle[resource_id] = {
                            'created_by': thread_id,
                            'created_at': time.time(),
                            'status': 'created'
                        }
                    
                    try:
                        # Use the resource (perform database operation)
                        with self.access_manager.connection_pool.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM leads")
                            result = cursor.fetchone()
                            
                            # Update resource status
                            with lifecycle_lock:
                                resource_lifecycle[resource_id]['status'] = 'used'
                                resource_lifecycle[resource_id]['used_at'] = time.time()
                            
                            thread_resources.append(resource_id)
                            
                            # Simulate resource usage
                            time.sleep(random.uniform(0.001, 0.01))
                    
                    finally:
                        # Clean up resource
                        with lifecycle_lock:
                            if resource_id in resource_lifecycle:
                                resource_lifecycle[resource_id]['status'] = 'cleaned'
                                resource_lifecycle[resource_id]['cleaned_at'] = time.time()
                
                self._record_thread_result(thread_id, 'resource_cleanup', len(thread_resources))
                
            except Exception as e:
                self._record_thread_result(thread_id, 'resource_cleanup', 0, e)
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=resource_worker,
                args=(thread_id,),
                name=f"ResourceThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)
        
        end_time = time.time()
        
        # Analyze resource lifecycle
        total_resources = len(resource_lifecycle)
        created_resources = sum(1 for r in resource_lifecycle.values() if r['status'] in ['created', 'used', 'cleaned'])
        used_resources = sum(1 for r in resource_lifecycle.values() if r['status'] in ['used', 'cleaned'])
        cleaned_resources = sum(1 for r in resource_lifecycle.values() if r['status'] == 'cleaned')
        
        print(f"Total resources: {total_resources}")
        print(f"Created resources: {created_resources}")
        print(f"Used resources: {used_resources}")
        print(f"Cleaned resources: {cleaned_resources}")
        print(f"Test duration: {end_time - start_time:.2f} seconds")
        
        # Check for resource leaks or cleanup issues
        leaked_resources = total_resources - cleaned_resources
        if leaked_resources > 0:
            print(f"WARNING: {leaked_resources} resources not properly cleaned up")
            
            # Show some examples
            for resource_id, lifecycle in resource_lifecycle.items():
                if lifecycle['status'] != 'cleaned':
                    print(f"  - {resource_id}: {lifecycle['status']}")
                    if len([r for r in resource_lifecycle.values() if r['status'] != 'cleaned']) >= 5:
                        break
        
        # Verify connection pool is still healthy
        pool_health = self.access_manager.connection_pool.health_check()
        print(f"Pool health after cleanup test: {pool_health['status']}")
        
        # Assertions
        expected_resources = num_threads * resources_per_thread
        self.assertEqual(total_resources, expected_resources)
        self.assertEqual(cleaned_resources, expected_resources, f"{leaked_resources} resources leaked")
        self.assertEqual(pool_health['status'], 'healthy')
    
    def _verify_database_integrity(self):
        """Verify database integrity after thread safety tests"""
        try:
            with self.lead_db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for basic integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                
                if integrity_result and integrity_result[0] != 'ok':
                    self.data_inconsistencies.append(f"Database integrity check failed: {integrity_result[0]}")
                
                # Check for foreign key violations
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if fk_violations:
                    self.data_inconsistencies.append(f"Foreign key violations: {len(fk_violations)}")
                
                # Check for duplicate primary keys
                cursor.execute("SELECT id, COUNT(*) as count FROM leads GROUP BY id HAVING count > 1")
                duplicate_ids = cursor.fetchall()
                
                if duplicate_ids:
                    self.data_inconsistencies.append(f"Duplicate primary keys: {len(duplicate_ids)}")
                
                print(f"Database integrity check: {len(self.data_inconsistencies)} issues found")
                
        except Exception as e:
            self.data_inconsistencies.append(f"Integrity check error: {str(e)}")
    
    def test_comprehensive_thread_safety(self):
        """Comprehensive thread safety test combining multiple scenarios"""
        print("\n=== Comprehensive Thread Safety Test ===")
        
        # Test parameters
        num_reader_threads = 10
        num_writer_threads = 10
        num_updater_threads = 5
        test_duration = 30  # seconds
        
        # Shared state
        test_active = threading.Event()
        test_active.set()
        
        # Statistics
        stats = {
            'reads': 0,
            'writes': 0,
            'updates': 0,
            'errors': 0
        }
        stats_lock = threading.Lock()
        
        def reader_worker(thread_id: int):
            """Worker that performs read operations"""
            local_reads = 0
            local_errors = 0
            
            while test_active.is_set():
                try:
                    # Perform various read operations
                    operations = [
                        lambda: self.lead_db.get_database_stats(),
                        lambda: self.lead_db.search_leads({'source': 'comprehensive_test'}),
                        lambda: len(list(self.lead_db.get_all_leads(limit=10)))
                    ]
                    
                    operation = random.choice(operations)
                    result = operation()
                    local_reads += 1
                    
                    time.sleep(random.uniform(0.001, 0.01))
                    
                except Exception as e:
                    local_errors += 1
                    if local_errors > 10:  # Too many errors, stop
                        break
            
            with stats_lock:
                stats['reads'] += local_reads
                stats['errors'] += local_errors
            
            self._record_thread_result(thread_id, 'comprehensive_reads', local_reads)
        
        def writer_worker(thread_id: int):
            """Worker that performs write operations"""
            local_writes = 0
            local_errors = 0
            
            while test_active.is_set():
                try:
                    # Create and insert lead
                    lead = {
                        'full_name': f'Comprehensive Test T{thread_id}W{local_writes}',
                        'email': f'comp_t{thread_id}w{local_writes}@test.com',
                        'company': f'Comprehensive Corp {thread_id}',
                        'source': 'comprehensive_test'
                    }
                    
                    lead_id = self.lead_db.add_lead(lead)
                    if lead_id:
                        local_writes += 1
                    
                    time.sleep(random.uniform(0.005, 0.02))
                    
                except Exception as e:
                    local_errors += 1
                    if local_errors > 10:
                        break
            
            with stats_lock:
                stats['writes'] += local_writes
                stats['errors'] += local_errors
            
            self._record_thread_result(thread_id, 'comprehensive_writes', local_writes)
        
        def updater_worker(thread_id: int):
            """Worker that performs update operations"""
            local_updates = 0
            local_errors = 0
            
            while test_active.is_set():
                try:
                    # Find a random lead to update
                    with self.lead_db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id FROM leads 
                            WHERE source = 'comprehensive_test' 
                            ORDER BY RANDOM() 
                            LIMIT 1
                        """)
                        row = cursor.fetchone()
                        
                        if row:
                            success = self.lead_db.update_lead(row['id'], {
                                'title': f'Updated by T{thread_id}U{local_updates}',
                                'updated_at': datetime.now().isoformat()
                            })
                            
                            if success:
                                local_updates += 1
                    
                    time.sleep(random.uniform(0.01, 0.05))
                    
                except Exception as e:
                    local_errors += 1
                    if local_errors > 10:
                        break
            
            with stats_lock:
                stats['updates'] += local_updates
                stats['errors'] += local_errors
            
            self._record_thread_result(thread_id, 'comprehensive_updates', local_updates)
        
        # Start all threads
        start_time = time.time()
        threads = []
        
        # Reader threads
        for i in range(num_reader_threads):
            thread = threading.Thread(
                target=reader_worker,
                args=(f"R{i}",),
                name=f"Reader-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Writer threads
        for i in range(num_writer_threads):
            thread = threading.Thread(
                target=writer_worker,
                args=(f"W{i}",),
                name=f"Writer-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Updater threads
        for i in range(num_updater_threads):
            thread = threading.Thread(
                target=updater_worker,
                args=(f"U{i}",),
                name=f"Updater-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Let test run for specified duration
        time.sleep(test_duration)
        test_active.clear()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Report results
        total_operations = stats['reads'] + stats['writes'] + stats['updates']
        throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = (stats['errors'] / total_operations * 100) if total_operations > 0 else 0
        
        print(f"Comprehensive test completed in {actual_duration:.2f} seconds")
        print(f"Total operations: {total_operations}")
        print(f"  - Reads: {stats['reads']}")
        print(f"  - Writes: {stats['writes']}")
        print(f"  - Updates: {stats['updates']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"Throughput: {throughput:.2f} ops/sec")
        print(f"Error rate: {error_rate:.2f}%")
        
        # Verify system health
        access_health = self.access_manager.health_check()
        pool_health = self.access_manager.connection_pool.health_check()
        
        print(f"Access manager health: {access_health['status']}")
        print(f"Connection pool health: {pool_health['status']}")
        
        # Final integrity check
        self._verify_database_integrity()
        
        # Assertions
        self.assertGreater(total_operations, 0)
        self.assertLess(error_rate, 5)  # Less than 5% error rate
        self.assertEqual(access_health['status'], 'healthy')
        self.assertEqual(pool_health['status'], 'healthy')
        self.assertEqual(len(self.data_inconsistencies), 0, "Data integrity violations detected")

def run_thread_safety_tests():
    """Run all thread safety tests"""
    print("Starting Thread Safety Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add thread safety tests
    suite.addTests(loader.loadTestsFromTestCase(ThreadSafetyTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("Thread Safety Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_thread_safety_tests()
    exit(0 if success else 1)