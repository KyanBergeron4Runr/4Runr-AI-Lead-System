#!/usr/bin/env python3
"""
Stress Tests for Concurrent Access Safety

This module contains comprehensive stress tests for the concurrent access
safety features of the lead database system.

Test Categories:
- High concurrency database operations
- Deadlock scenarios and recovery
- Connection pool stress testing
- Transaction rollback scenarios
- Resource contention testing
- Performance under load
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
from typing import List, Dict, Any, Callable
import uuid
from datetime import datetime, timedelta
import json

# Import our modules
from database_connection_pool import DatabaseConnectionPool, get_connection_pool, close_connection_pool
from concurrent_access_manager import ConcurrentAccessManager, OperationPriority, LockType
from lead_database import LeadDatabase

class ConcurrentAccessStressTests(unittest.TestCase):
    """Stress tests for concurrent access safety"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_concurrent.db")
        
        # Initialize database
        self.lead_db = LeadDatabase(self.db_path)
        
        # Initialize concurrent access manager
        self.access_manager = ConcurrentAccessManager(
            db_path=self.db_path,
            max_concurrent_operations=20,
            operation_timeout=30,
            deadlock_detection_interval=1
        )
        
        # Test data
        self.test_leads = self._generate_test_leads(1000)
        
        # Statistics tracking
        self.test_stats = {
            'operations_completed': 0,
            'operations_failed': 0,
            'deadlocks_detected': 0,
            'timeouts': 0,
            'data_corruption_detected': 0
        }
        self.stats_lock = threading.Lock()
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            self.access_manager.shutdown()
            close_connection_pool()
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def _generate_test_leads(self, count: int) -> List[Dict[str, Any]]:
        """Generate test lead data"""
        leads = []
        companies = ["TechCorp", "DataSys", "CloudInc", "AILabs", "DevTools"]
        domains = ["techcorp.com", "datasys.io", "cloudinc.net", "ailabs.ai", "devtools.dev"]
        
        for i in range(count):
            company = random.choice(companies)
            domain = random.choice(domains)
            
            lead = {
                'full_name': f'Test User {i}',
                'email': f'user{i}@{domain}',
                'company': f'{company} {i // 100}',
                'linkedin_url': f'https://linkedin.com/in/testuser{i}',
                'title': random.choice(['CEO', 'CTO', 'VP Engineering', 'Director', 'Manager']),
                'location': random.choice(['San Francisco', 'New York', 'Austin', 'Seattle', 'Boston']),
                'industry': random.choice(['Technology', 'Healthcare', 'Finance', 'Education', 'Retail']),
                'source': 'stress_test'
            }
            leads.append(lead)
        
        return leads
    
    def _update_stats(self, stat_name: str, increment: int = 1):
        """Thread-safe statistics update"""
        with self.stats_lock:
            self.test_stats[stat_name] += increment
    
    def test_high_concurrency_inserts(self):
        """Test high concurrency lead insertions"""
        print("\n=== Testing High Concurrency Inserts ===")
        
        num_threads = 50
        leads_per_thread = 20
        
        def insert_leads(thread_id: int, leads: List[Dict[str, Any]]):
            """Insert leads in a thread"""
            try:
                for i, lead in enumerate(leads):
                    # Add thread and iteration info to make leads unique
                    lead_copy = lead.copy()
                    lead_copy['full_name'] = f"{lead['full_name']} T{thread_id}I{i}"
                    lead_copy['email'] = f"t{thread_id}i{i}_{lead['email']}"
                    
                    # Use the access manager for thread-safe operations
                    def add_lead_operation():
                        return self.lead_db.add_lead(lead_copy)
                    
                    result = self.access_manager.execute_operation(
                        operation_type="add_lead",
                        callback=add_lead_operation,
                        priority=OperationPriority.NORMAL,
                        timeout=30
                    )
                    
                    if result:
                        self._update_stats('operations_completed')
                    
                    # Small random delay to increase contention
                    time.sleep(random.uniform(0.001, 0.01))
                    
            except Exception as e:
                print(f"Thread {thread_id} error: {e}")
                self._update_stats('operations_failed')
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread_leads = self.test_leads[
                thread_id * leads_per_thread:(thread_id + 1) * leads_per_thread
            ]
            thread = threading.Thread(
                target=insert_leads,
                args=(thread_id, thread_leads),
                name=f"InsertThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=120)  # 2 minute timeout
        
        end_time = time.time()
        
        # Verify results
        stats = self.access_manager.get_stats()
        db_stats = self.lead_db.get_database_stats()
        
        print(f"Test completed in {end_time - start_time:.2f} seconds")
        print(f"Operations completed: {self.test_stats['operations_completed']}")
        print(f"Operations failed: {self.test_stats['operations_failed']}")
        print(f"Total leads in database: {db_stats['total_leads']}")
        print(f"Concurrent access stats: {stats['concurrent_access_stats']}")
        
        # Assertions
        self.assertGreater(self.test_stats['operations_completed'], 0)
        self.assertGreater(db_stats['total_leads'], 0)
        
        # Check for data integrity
        self._verify_data_integrity()
    
    def test_mixed_operations_stress(self):
        """Test mixed read/write operations under stress"""
        print("\n=== Testing Mixed Operations Stress ===")
        
        # Pre-populate database
        for i, lead in enumerate(self.test_leads[:100]):
            lead_copy = lead.copy()
            lead_copy['full_name'] = f"Prepop {lead['full_name']}"
            lead_copy['email'] = f"prepop_{lead['email']}"
            self.lead_db.add_lead(lead_copy)
        
        num_threads = 30
        operations_per_thread = 50
        
        def mixed_operations(thread_id: int):
            """Perform mixed database operations"""
            try:
                for i in range(operations_per_thread):
                    operation_type = random.choice(['insert', 'update', 'search', 'get'])
                    
                    if operation_type == 'insert':
                        # Insert new lead
                        lead = random.choice(self.test_leads).copy()
                        lead['full_name'] = f"Mixed T{thread_id}I{i} {lead['full_name']}"
                        lead['email'] = f"mixed_t{thread_id}i{i}_{lead['email']}"
                        
                        def add_operation():
                            return self.lead_db.add_lead(lead)
                        
                        self.access_manager.execute_operation(
                            operation_type="add_lead",
                            callback=add_operation,
                            priority=OperationPriority.NORMAL
                        )
                    
                    elif operation_type == 'update':
                        # Update existing lead
                        def update_operation():
                            # Get a random lead to update
                            with self.lead_db.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT id FROM leads ORDER BY RANDOM() LIMIT 1")
                                row = cursor.fetchone()
                                if row:
                                    return self.lead_db.update_lead(row['id'], {
                                        'title': f'Updated by T{thread_id}I{i}',
                                        'updated_at': datetime.now().isoformat()
                                    })
                            return False
                        
                        self.access_manager.execute_operation(
                            operation_type="update_lead",
                            callback=update_operation,
                            priority=OperationPriority.NORMAL
                        )
                    
                    elif operation_type == 'search':
                        # Search leads
                        def search_operation():
                            search_terms = random.choice(['TechCorp', 'CEO', 'San Francisco'])
                            return self.lead_db.search_leads({'company': search_terms})
                        
                        self.access_manager.execute_operation(
                            operation_type="search_leads",
                            callback=search_operation,
                            priority=OperationPriority.LOW
                        )
                    
                    elif operation_type == 'get':
                        # Get specific lead
                        def get_operation():
                            with self.lead_db.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("SELECT id FROM leads ORDER BY RANDOM() LIMIT 1")
                                row = cursor.fetchone()
                                if row:
                                    return self.lead_db.get_lead(row['id'])
                            return None
                        
                        self.access_manager.execute_operation(
                            operation_type="get_lead",
                            callback=get_operation,
                            priority=OperationPriority.LOW
                        )
                    
                    self._update_stats('operations_completed')
                    
                    # Random delay
                    time.sleep(random.uniform(0.001, 0.005))
                    
            except Exception as e:
                print(f"Mixed operations thread {thread_id} error: {e}")
                self._update_stats('operations_failed')
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=mixed_operations,
                args=(thread_id,),
                name=f"MixedOpsThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=180)  # 3 minute timeout
        
        end_time = time.time()
        
        # Report results
        stats = self.access_manager.get_stats()
        db_stats = self.lead_db.get_database_stats()
        
        print(f"Mixed operations test completed in {end_time - start_time:.2f} seconds")
        print(f"Operations completed: {self.test_stats['operations_completed']}")
        print(f"Operations failed: {self.test_stats['operations_failed']}")
        print(f"Final database stats: {db_stats}")
        print(f"Deadlocks detected: {stats['concurrent_access_stats']['deadlocks_detected']}")
        
        # Verify data integrity
        self._verify_data_integrity()
    
    def test_deadlock_scenarios(self):
        """Test deadlock detection and resolution"""
        print("\n=== Testing Deadlock Scenarios ===")
        
        # Create resources that will cause deadlocks
        resource_a = "lead_table_section_1"
        resource_b = "lead_table_section_2"
        
        deadlock_detected = threading.Event()
        
        def deadlock_thread_1():
            """Thread that acquires A then B"""
            try:
                with self.access_manager.acquire_resource_lock(resource_a, LockType.EXCLUSIVE):
                    time.sleep(0.1)  # Hold lock for a bit
                    with self.access_manager.acquire_resource_lock(resource_b, LockType.EXCLUSIVE, timeout=5):
                        time.sleep(0.1)
                        self._update_stats('operations_completed')
            except Exception as e:
                print(f"Deadlock thread 1 error: {e}")
                if "deadlock" in str(e).lower():
                    deadlock_detected.set()
                self._update_stats('operations_failed')
        
        def deadlock_thread_2():
            """Thread that acquires B then A"""
            try:
                with self.access_manager.acquire_resource_lock(resource_b, LockType.EXCLUSIVE):
                    time.sleep(0.1)  # Hold lock for a bit
                    with self.access_manager.acquire_resource_lock(resource_a, LockType.EXCLUSIVE, timeout=5):
                        time.sleep(0.1)
                        self._update_stats('operations_completed')
            except Exception as e:
                print(f"Deadlock thread 2 error: {e}")
                if "deadlock" in str(e).lower():
                    deadlock_detected.set()
                self._update_stats('operations_failed')
        
        # Start deadlock scenario
        thread1 = threading.Thread(target=deadlock_thread_1, name="DeadlockThread1")
        thread2 = threading.Thread(target=deadlock_thread_2, name="DeadlockThread2")
        
        start_time = time.time()
        thread1.start()
        thread2.start()
        
        # Wait for threads or deadlock detection
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        end_time = time.time()
        
        # Check results
        stats = self.access_manager.get_stats()
        deadlock_history = self.access_manager.get_deadlock_history()
        
        print(f"Deadlock test completed in {end_time - start_time:.2f} seconds")
        print(f"Deadlocks detected: {len(deadlock_history)}")
        print(f"Operations completed: {self.test_stats['operations_completed']}")
        print(f"Operations failed: {self.test_stats['operations_failed']}")
        
        if deadlock_history:
            print("Deadlock details:")
            for dl in deadlock_history:
                print(f"  - {dl['deadlock_id']}: {dl['resolution_action']}")
        
        # At least one operation should fail due to deadlock resolution
        self.assertGreater(self.test_stats['operations_failed'], 0)
    
    def test_connection_pool_stress(self):
        """Test connection pool under stress"""
        print("\n=== Testing Connection Pool Stress ===")
        
        num_threads = 100
        connections_per_thread = 10
        
        def connection_stress(thread_id: int):
            """Stress test connection acquisition and release"""
            try:
                for i in range(connections_per_thread):
                    # Get connection from pool
                    with self.access_manager.connection_pool.get_connection(timeout=10) as conn:
                        # Perform a simple query
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM leads")
                        result = cursor.fetchone()
                        
                        # Small delay while holding connection
                        time.sleep(random.uniform(0.001, 0.01))
                        
                        self._update_stats('operations_completed')
                        
            except Exception as e:
                print(f"Connection stress thread {thread_id} error: {e}")
                self._update_stats('operations_failed')
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=connection_stress,
                args=(thread_id,),
                name=f"ConnStressThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)
        
        end_time = time.time()
        
        # Check pool health
        pool_stats = self.access_manager.connection_pool.get_pool_stats()
        pool_health = self.access_manager.connection_pool.health_check()
        
        print(f"Connection pool stress test completed in {end_time - start_time:.2f} seconds")
        print(f"Operations completed: {self.test_stats['operations_completed']}")
        print(f"Operations failed: {self.test_stats['operations_failed']}")
        print(f"Pool stats: {pool_stats}")
        print(f"Pool health: {pool_health['status']}")
        
        # Verify pool is still healthy
        self.assertEqual(pool_health['status'], 'healthy')
        self.assertGreater(self.test_stats['operations_completed'], 0)
    
    def test_transaction_rollback_stress(self):
        """Test transaction rollback under stress"""
        print("\n=== Testing Transaction Rollback Stress ===")
        
        num_threads = 20
        transactions_per_thread = 10
        
        def transaction_stress(thread_id: int):
            """Stress test transactions with intentional failures"""
            try:
                for i in range(transactions_per_thread):
                    def transaction_operation():
                        with self.access_manager.connection_pool.get_connection() as conn:
                            # Start transaction
                            conn.execute("BEGIN IMMEDIATE")
                            
                            try:
                                # Insert a lead
                                lead = random.choice(self.test_leads).copy()
                                lead['full_name'] = f"Trans T{thread_id}I{i} {lead['full_name']}"
                                lead['email'] = f"trans_t{thread_id}i{i}_{lead['email']}"
                                
                                cursor = conn.cursor()
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
                                
                                # Randomly cause some transactions to fail
                                if random.random() < 0.3:  # 30% failure rate
                                    raise RuntimeError("Intentional transaction failure")
                                
                                # Commit transaction
                                conn.execute("COMMIT")
                                return True
                                
                            except Exception as e:
                                # Rollback transaction
                                conn.execute("ROLLBACK")
                                if "Intentional" not in str(e):
                                    raise
                                return False
                    
                    result = self.access_manager.execute_operation(
                        operation_type="transaction_test",
                        callback=transaction_operation,
                        priority=OperationPriority.NORMAL
                    )
                    
                    if result:
                        self._update_stats('operations_completed')
                    else:
                        self._update_stats('operations_failed')
                        
            except Exception as e:
                print(f"Transaction stress thread {thread_id} error: {e}")
                self._update_stats('operations_failed')
        
        # Start threads
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=transaction_stress,
                args=(thread_id,),
                name=f"TransStressThread-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=120)
        
        end_time = time.time()
        
        # Verify database integrity after rollbacks
        db_stats = self.lead_db.get_database_stats()
        
        print(f"Transaction rollback stress test completed in {end_time - start_time:.2f} seconds")
        print(f"Operations completed: {self.test_stats['operations_completed']}")
        print(f"Operations failed: {self.test_stats['operations_failed']}")
        print(f"Final database stats: {db_stats}")
        
        # Verify data integrity
        self._verify_data_integrity()
        
        # Should have both successes and failures
        self.assertGreater(self.test_stats['operations_completed'], 0)
        self.assertGreater(self.test_stats['operations_failed'], 0)
    
    def test_performance_under_load(self):
        """Test system performance under heavy load"""
        print("\n=== Testing Performance Under Load ===")
        
        # Performance test parameters
        num_threads = 50
        operations_per_thread = 100
        test_duration = 60  # seconds
        
        performance_data = {
            'operation_times': [],
            'throughput_samples': [],
            'error_rates': []
        }
        performance_lock = threading.Lock()
        
        stop_event = threading.Event()
        
        def performance_worker(thread_id: int):
            """Worker thread for performance testing"""
            local_ops = 0
            local_errors = 0
            
            while not stop_event.is_set():
                try:
                    start_time = time.time()
                    
                    # Perform a database operation
                    lead = random.choice(self.test_leads).copy()
                    lead['full_name'] = f"Perf T{thread_id} {lead['full_name']} {local_ops}"
                    lead['email'] = f"perf_t{thread_id}_{local_ops}_{lead['email']}"
                    
                    def perf_operation():
                        return self.lead_db.add_lead(lead)
                    
                    result = self.access_manager.execute_operation(
                        operation_type="performance_test",
                        callback=perf_operation,
                        priority=OperationPriority.NORMAL,
                        timeout=10
                    )
                    
                    end_time = time.time()
                    operation_time = end_time - start_time
                    
                    with performance_lock:
                        performance_data['operation_times'].append(operation_time)
                    
                    local_ops += 1
                    
                    if local_ops >= operations_per_thread:
                        break
                        
                except Exception as e:
                    local_errors += 1
                    if local_errors > 10:  # Too many errors, stop this thread
                        break
            
            self._update_stats('operations_completed', local_ops)
            self._update_stats('operations_failed', local_errors)
        
        def throughput_monitor():
            """Monitor throughput during the test"""
            last_completed = 0
            
            while not stop_event.is_set():
                time.sleep(5)  # Sample every 5 seconds
                
                current_completed = self.test_stats['operations_completed']
                throughput = (current_completed - last_completed) / 5.0  # ops per second
                
                with performance_lock:
                    performance_data['throughput_samples'].append(throughput)
                
                last_completed = current_completed
        
        # Start performance test
        start_time = time.time()
        threads = []
        
        # Start worker threads
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=performance_worker,
                args=(thread_id,),
                name=f"PerfWorker-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Start throughput monitor
        monitor_thread = threading.Thread(target=throughput_monitor, name="ThroughputMonitor")
        monitor_thread.start()
        
        # Let test run for specified duration
        time.sleep(test_duration)
        stop_event.set()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)
        monitor_thread.join(timeout=5)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate performance metrics
        with performance_lock:
            operation_times = performance_data['operation_times']
            throughput_samples = performance_data['throughput_samples']
        
        if operation_times:
            avg_operation_time = sum(operation_times) / len(operation_times)
            min_operation_time = min(operation_times)
            max_operation_time = max(operation_times)
            
            # Calculate percentiles
            sorted_times = sorted(operation_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_operation_time = min_operation_time = max_operation_time = 0
            p50 = p95 = p99 = 0
        
        if throughput_samples:
            avg_throughput = sum(throughput_samples) / len(throughput_samples)
            max_throughput = max(throughput_samples)
        else:
            avg_throughput = max_throughput = 0
        
        total_operations = self.test_stats['operations_completed'] + self.test_stats['operations_failed']
        overall_throughput = total_operations / actual_duration if actual_duration > 0 else 0
        error_rate = (self.test_stats['operations_failed'] / total_operations * 100) if total_operations > 0 else 0
        
        # Get system stats
        access_stats = self.access_manager.get_stats()
        pool_stats = self.access_manager.connection_pool.get_pool_stats()
        
        print(f"Performance test completed in {actual_duration:.2f} seconds")
        print(f"Total operations: {total_operations}")
        print(f"Operations completed: {self.test_stats['operations_completed']}")
        print(f"Operations failed: {self.test_stats['operations_failed']}")
        print(f"Error rate: {error_rate:.2f}%")
        print(f"Overall throughput: {overall_throughput:.2f} ops/sec")
        print(f"Average throughput: {avg_throughput:.2f} ops/sec")
        print(f"Peak throughput: {max_throughput:.2f} ops/sec")
        print(f"Operation time - Avg: {avg_operation_time:.3f}s, Min: {min_operation_time:.3f}s, Max: {max_operation_time:.3f}s")
        print(f"Operation time - P50: {p50:.3f}s, P95: {p95:.3f}s, P99: {p99:.3f}s")
        print(f"Peak concurrent operations: {access_stats['concurrent_access_stats']['peak_concurrent_operations']}")
        print(f"Pool utilization: {pool_stats['pool_utilization']:.2f}")
        
        # Performance assertions
        self.assertGreater(total_operations, 0)
        self.assertLess(error_rate, 10)  # Less than 10% error rate
        self.assertGreater(overall_throughput, 1)  # At least 1 op/sec
        self.assertLess(avg_operation_time, 5)  # Average operation under 5 seconds
    
    def _verify_data_integrity(self):
        """Verify database data integrity after stress tests"""
        try:
            with self.lead_db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for duplicate emails (should not exist due to duplicate detection)
                cursor.execute("""
                    SELECT email, COUNT(*) as count 
                    FROM leads 
                    WHERE email IS NOT NULL AND email != ''
                    GROUP BY email 
                    HAVING count > 1
                """)
                duplicates = cursor.fetchall()
                
                if duplicates:
                    print(f"WARNING: Found {len(duplicates)} duplicate emails")
                    for dup in duplicates[:5]:  # Show first 5
                        print(f"  - {dup['email']}: {dup['count']} occurrences")
                    self._update_stats('data_corruption_detected', len(duplicates))
                
                # Check for NULL required fields
                cursor.execute("SELECT COUNT(*) as count FROM leads WHERE full_name IS NULL OR full_name = ''")
                null_names = cursor.fetchone()['count']
                
                if null_names > 0:
                    print(f"WARNING: Found {null_names} leads with NULL/empty names")
                    self._update_stats('data_corruption_detected', null_names)
                
                # Check for malformed data
                cursor.execute("SELECT COUNT(*) as count FROM leads WHERE created_at IS NULL")
                null_dates = cursor.fetchone()['count']
                
                if null_dates > 0:
                    print(f"WARNING: Found {null_dates} leads with NULL created_at")
                    self._update_stats('data_corruption_detected', null_dates)
                
                # Verify foreign key constraints (if any)
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if fk_violations:
                    print(f"WARNING: Found {len(fk_violations)} foreign key violations")
                    self._update_stats('data_corruption_detected', len(fk_violations))
                
                print(f"Data integrity check completed. Issues found: {self.test_stats['data_corruption_detected']}")
                
        except Exception as e:
            print(f"Error during data integrity check: {e}")
            self._update_stats('data_corruption_detected', 1)

class ConcurrentAccessBenchmarks(unittest.TestCase):
    """Benchmark tests for concurrent access performance"""
    
    def setUp(self):
        """Set up benchmark environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "benchmark.db")
        
        # Initialize with different configurations for comparison
        self.configs = {
            'default': {
                'max_concurrent_operations': 10,
                'connection_timeout': 30,
                'enable_wal_mode': True
            },
            'high_concurrency': {
                'max_concurrent_operations': 50,
                'connection_timeout': 10,
                'enable_wal_mode': True
            },
            'low_latency': {
                'max_concurrent_operations': 5,
                'connection_timeout': 5,
                'enable_wal_mode': True
            }
        }
        
        self.benchmark_results = {}
    
    def tearDown(self):
        """Clean up benchmark environment"""
        try:
            close_connection_pool()
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Benchmark cleanup error: {e}")
    
    def test_configuration_benchmarks(self):
        """Benchmark different configuration settings"""
        print("\n=== Configuration Benchmarks ===")
        
        for config_name, config in self.configs.items():
            print(f"\nTesting configuration: {config_name}")
            
            # Create fresh database for each config
            db_path = os.path.join(self.test_dir, f"bench_{config_name}.db")
            lead_db = LeadDatabase(db_path)
            
            # Create access manager with this config
            access_manager = ConcurrentAccessManager(
                db_path=db_path,
                **config
            )
            
            # Run benchmark
            result = self._run_benchmark(lead_db, access_manager, config_name)
            self.benchmark_results[config_name] = result
            
            # Cleanup
            access_manager.shutdown()
            
            print(f"Results for {config_name}:")
            print(f"  - Throughput: {result['throughput']:.2f} ops/sec")
            print(f"  - Average latency: {result['avg_latency']:.3f}s")
            print(f"  - Error rate: {result['error_rate']:.2f}%")
        
        # Compare results
        print("\n=== Benchmark Comparison ===")
        best_throughput = max(self.benchmark_results.values(), key=lambda x: x['throughput'])
        best_latency = min(self.benchmark_results.values(), key=lambda x: x['avg_latency'])
        
        print(f"Best throughput: {best_throughput['config']} ({best_throughput['throughput']:.2f} ops/sec)")
        print(f"Best latency: {best_latency['config']} ({best_latency['avg_latency']:.3f}s)")
    
    def _run_benchmark(self, lead_db: LeadDatabase, access_manager: ConcurrentAccessManager, config_name: str) -> Dict[str, Any]:
        """Run a benchmark test with given configuration"""
        num_threads = 20
        operations_per_thread = 50
        test_duration = 30  # seconds
        
        completed_operations = 0
        failed_operations = 0
        operation_times = []
        stats_lock = threading.Lock()
        
        def benchmark_worker(thread_id: int):
            nonlocal completed_operations, failed_operations
            
            local_completed = 0
            local_failed = 0
            local_times = []
            
            for i in range(operations_per_thread):
                try:
                    start_time = time.time()
                    
                    # Create test lead
                    lead = {
                        'full_name': f'Benchmark User {config_name} T{thread_id}I{i}',
                        'email': f'bench_{config_name}_t{thread_id}i{i}@test.com',
                        'company': f'Benchmark Corp {thread_id}',
                        'source': 'benchmark'
                    }
                    
                    def bench_operation():
                        return lead_db.add_lead(lead)
                    
                    result = access_manager.execute_operation(
                        operation_type="benchmark_add",
                        callback=bench_operation,
                        priority=OperationPriority.NORMAL,
                        timeout=10
                    )
                    
                    end_time = time.time()
                    operation_time = end_time - start_time
                    
                    if result:
                        local_completed += 1
                        local_times.append(operation_time)
                    else:
                        local_failed += 1
                        
                except Exception as e:
                    local_failed += 1
            
            # Update global stats
            with stats_lock:
                completed_operations += local_completed
                failed_operations += local_failed
                operation_times.extend(local_times)
        
        # Run benchmark
        start_time = time.time()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(
                target=benchmark_worker,
                args=(thread_id,),
                name=f"BenchWorker-{thread_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=test_duration + 10)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate metrics
        total_operations = completed_operations + failed_operations
        throughput = completed_operations / actual_duration if actual_duration > 0 else 0
        error_rate = (failed_operations / total_operations * 100) if total_operations > 0 else 0
        avg_latency = sum(operation_times) / len(operation_times) if operation_times else 0
        
        return {
            'config': config_name,
            'throughput': throughput,
            'avg_latency': avg_latency,
            'error_rate': error_rate,
            'total_operations': total_operations,
            'duration': actual_duration
        }

def run_stress_tests():
    """Run all stress tests"""
    print("Starting Concurrent Access Stress Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add stress tests
    suite.addTests(loader.loadTestsFromTestCase(ConcurrentAccessStressTests))
    suite.addTests(loader.loadTestsFromTestCase(ConcurrentAccessBenchmarks))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("Stress Test Summary:")
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
    success = run_stress_tests()
    exit(0 if success else 1)