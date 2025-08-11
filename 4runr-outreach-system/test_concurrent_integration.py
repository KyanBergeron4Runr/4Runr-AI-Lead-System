#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Concurrent Access Safety

This module tests the complete integration of concurrent access safety features
with the lead database system, including real-world scenarios and edge cases.

Test Scenarios:
- Multi-agent concurrent operations
- Database migration with concurrent access
- Airtable sync with concurrent operations
- Error recovery and rollback scenarios
- Performance under realistic load
"""

import unittest
import threading
import time
import random
import sqlite3
import tempfile
import os
import shutil
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta

# Import our modules
from lead_database import LeadDatabase
from database_connection_pool import get_connection_pool, close_connection_pool
from concurrent_access_manager import get_concurrent_access_manager, OperationPriority
from migration_manager import MigrationManager
from airtable_sync_manager import AirtableSyncManager

class ConcurrentIntegrationTests(unittest.TestCase):
    """Integration tests for concurrent access safety"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "integration_test.db")
        
        # Initialize components
        self.lead_db = LeadDatabase(self.db_path)
        self.access_manager = get_concurrent_access_manager(
            db_path=self.db_path,
            max_concurrent_operations=25,
            deadlock_detection_interval=2
        )
        
        # Test data
        self.test_companies = [
            "TechCorp Solutions", "DataFlow Systems", "CloudScale Inc",
            "AI Innovations", "DevOps Masters", "CyberSec Pro",
            "FinTech Leaders", "HealthTech Plus", "EduTech Global"
        ]
        
        self.test_domains = [
            "techcorp.com", "dataflow.io", "cloudscale.net",
            "aiinnovations.ai", "devopsmaster.dev", "cybersecpro.com",
            "fintechleaders.finance", "healthtechplus.health", "edutechglobal.edu"
        ]
        
        # Statistics tracking
        self.integration_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'concurrent_conflicts': 0,
            'data_integrity_issues': 0,
            'performance_issues': 0
        }
        self.stats_lock = threading.Lock()
    
    def tearDown(self):
        """Clean up integration test environment"""
        try:
            self.access_manager.shutdown()
            close_connection_pool()
            shutil.rmtree(self.test_dir)
        except Exception as e:
            print(f"Integration test cleanup error: {e}")
    
    def _update_stats(self, stat_name: str, increment: int = 1):
        """Thread-safe statistics update"""
        with self.stats_lock:
            self.integration_stats[stat_name] += increment
    
    def _generate_realistic_lead(self, company_index: int, lead_index: int) -> Dict[str, Any]:
        """Generate realistic lead data"""
        company = self.test_companies[company_index % len(self.test_companies)]
        domain = self.test_domains[company_index % len(self.test_domains)]
        
        titles = [
            "Chief Executive Officer", "Chief Technology Officer", "VP of Engineering",
            "Director of Sales", "Marketing Manager", "Product Manager",
            "Senior Developer", "Data Scientist", "DevOps Engineer"
        ]
        
        locations = [
            "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA",
            "Boston, MA", "Denver, CO", "Chicago, IL", "Los Angeles, CA"
        ]
        
        industries = [
            "Technology", "Software", "Healthcare", "Finance", "Education",
            "E-commerce", "Manufacturing", "Consulting", "Media"
        ]
        
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Emily"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        return {
            'full_name': full_name,
            'email': f"{first_name.lower()}.{last_name.lower()}@{domain}",
            'company': company,
            'company_website': f"https://{domain}",
            'linkedin_url': f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{lead_index}",
            'title': random.choice(titles),
            'location': random.choice(locations),
            'industry': random.choice(industries),
            'company_size': random.choice(["1-10", "11-50", "51-200", "201-1000", "1000+"]),
            'source': 'integration_test',
            'verified': random.choice([True, False]),
            'enriched': random.choice([True, False]),
            'needs_enrichment': random.choice([True, False]),
            'status': random.choice(['new', 'contacted', 'qualified', 'converted']),
            'raw_data': {
                'scraping_session': f"session_{company_index}_{lead_index}",
                'confidence_score': random.uniform(0.7, 1.0),
                'data_sources': ['linkedin', 'company_website', 'crunchbase']
            }
        }
    
    def test_multi_agent_simulation(self):
        """Simulate multiple agents working concurrently"""
        print("\n=== Multi-Agent Simulation Test ===")
        
        # Simulate different types of agents
        num_scraper_agents = 5
        num_enricher_agents = 3
        num_sync_agents = 2
        
        test_duration = 45  # seconds
        stop_event = threading.Event()
        
        def scraper_agent(agent_id: int):
            """Simulate a scraper agent adding new leads"""
            leads_scraped = 0
            
            while not stop_event.is_set():
                try:
                    # Generate leads for a company
                    company_index = agent_id
                    lead = self._generate_realistic_lead(company_index, leads_scraped)
                    
                    # Add lead with high priority (new data)
                    def scrape_operation():
                        return self.lead_db.add_lead(lead)
                    
                    lead_id = self.access_manager.execute_operation(
                        operation_type="scraper_add_lead",
                        callback=scrape_operation,
                        priority=OperationPriority.HIGH,
                        timeout=20
                    )
                    
                    if lead_id:
                        leads_scraped += 1
                        self._update_stats('successful_operations')
                    else:
                        self._update_stats('failed_operations')
                    
                    self._update_stats('total_operations')
                    
                    # Realistic scraping delay
                    time.sleep(random.uniform(0.5, 2.0))
                    
                except Exception as e:
                    print(f"Scraper agent {agent_id} error: {e}")
                    self._update_stats('failed_operations')
                    time.sleep(1)  # Back off on error
            
            print(f"Scraper agent {agent_id} scraped {leads_scraped} leads")
        
        def enricher_agent(agent_id: int):
            """Simulate an enricher agent updating lead data"""
            leads_enriched = 0
            
            while not stop_event.is_set():
                try:
                    # Find leads that need enrichment
                    def find_leads_operation():
                        with self.lead_db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT id FROM leads 
                                WHERE needs_enrichment = 1 
                                AND source = 'integration_test'
                                ORDER BY RANDOM() 
                                LIMIT 5
                            """)
                            return [row['id'] for row in cursor.fetchall()]
                    
                    lead_ids = self.access_manager.execute_operation(
                        operation_type="enricher_find_leads",
                        callback=find_leads_operation,
                        priority=OperationPriority.NORMAL,
                        timeout=10
                    )
                    
                    # Enrich found leads
                    for lead_id in lead_ids:
                        enrichment_data = {
                            'enriched': True,
                            'needs_enrichment': False,
                            'enriched_at': datetime.now().isoformat(),
                            'title': f'Enriched Title {agent_id}',
                            'industry': 'Enriched Industry',
                            'company_size': random.choice(["51-200", "201-1000", "1000+"])
                        }
                        
                        def enrich_operation():
                            return self.lead_db.update_lead(lead_id, enrichment_data)
                        
                        success = self.access_manager.execute_operation(
                            operation_type="enricher_update_lead",
                            callback=enrich_operation,
                            priority=OperationPriority.NORMAL,
                            timeout=15
                        )
                        
                        if success:
                            leads_enriched += 1
                            self._update_stats('successful_operations')
                        else:
                            self._update_stats('failed_operations')
                        
                        self._update_stats('total_operations')
                    
                    # Realistic enrichment delay
                    time.sleep(random.uniform(1.0, 3.0))
                    
                except Exception as e:
                    print(f"Enricher agent {agent_id} error: {e}")
                    self._update_stats('failed_operations')
                    time.sleep(2)
            
            print(f"Enricher agent {agent_id} enriched {leads_enriched} leads")
        
        def sync_agent(agent_id: int):
            """Simulate a sync agent marking leads for sync"""
            leads_synced = 0
            
            while not stop_event.is_set():
                try:
                    # Find leads that need syncing
                    def find_sync_leads_operation():
                        with self.lead_db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT id FROM leads 
                                WHERE sync_pending = 1 
                                AND source = 'integration_test'
                                ORDER BY created_at ASC 
                                LIMIT 10
                            """)
                            return [row['id'] for row in cursor.fetchall()]
                    
                    lead_ids = self.access_manager.execute_operation(
                        operation_type="sync_find_leads",
                        callback=find_sync_leads_operation,
                        priority=OperationPriority.LOW,
                        timeout=10
                    )
                    
                    # Process sync for found leads
                    for lead_id in lead_ids:
                        sync_data = {
                            'sync_pending': False,
                            'airtable_synced': True,
                            'airtable_id': f'rec{agent_id}{leads_synced}{random.randint(1000, 9999)}',
                            'last_sync_attempt': datetime.now().isoformat()
                        }
                        
                        def sync_operation():
                            return self.lead_db.update_lead(lead_id, sync_data)
                        
                        success = self.access_manager.execute_operation(
                            operation_type="sync_update_lead",
                            callback=sync_operation,
                            priority=OperationPriority.LOW,
                            timeout=15
                        )
                        
                        if success:
                            leads_synced += 1
                            self._update_stats('successful_operations')
                        else:
                            self._update_stats('failed_operations')
                        
                        self._update_stats('total_operations')
                    
                    # Realistic sync delay
                    time.sleep(random.uniform(2.0, 5.0))
                    
                except Exception as e:
                    print(f"Sync agent {agent_id} error: {e}")
                    self._update_stats('failed_operations')
                    time.sleep(3)
            
            print(f"Sync agent {agent_id} processed {leads_synced} leads")
        
        # Start all agents
        start_time = time.time()
        threads = []
        
        # Start scraper agents
        for i in range(num_scraper_agents):
            thread = threading.Thread(
                target=scraper_agent,
                args=(i,),
                name=f"ScraperAgent-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Start enricher agents
        for i in range(num_enricher_agents):
            thread = threading.Thread(
                target=enricher_agent,
                args=(i,),
                name=f"EnricherAgent-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Start sync agents
        for i in range(num_sync_agents):
            thread = threading.Thread(
                target=sync_agent,
                args=(i,),
                name=f"SyncAgent-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Let simulation run
        time.sleep(test_duration)
        stop_event.set()
        
        # Wait for all agents to stop
        for thread in threads:
            thread.join(timeout=10)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Analyze results
        db_stats = self.lead_db.get_database_stats()
        access_stats = self.access_manager.get_stats()
        pool_stats = self.access_manager.connection_pool.get_pool_stats()
        
        print(f"Multi-agent simulation completed in {actual_duration:.2f} seconds")
        print(f"Total operations: {self.integration_stats['total_operations']}")
        print(f"Successful operations: {self.integration_stats['successful_operations']}")
        print(f"Failed operations: {self.integration_stats['failed_operations']}")
        print(f"Success rate: {(self.integration_stats['successful_operations'] / max(1, self.integration_stats['total_operations']) * 100):.2f}%")
        print(f"Database stats: {db_stats}")
        print(f"Concurrent operations peak: {access_stats['concurrent_access_stats']['peak_concurrent_operations']}")
        print(f"Deadlocks detected: {access_stats['concurrent_access_stats']['deadlocks_detected']}")
        print(f"Pool utilization: {pool_stats['pool_utilization']:.2f}")
        
        # Verify data integrity
        self._verify_integration_data_integrity()
        
        # Assertions
        self.assertGreater(self.integration_stats['total_operations'], 0)
        self.assertGreater(self.integration_stats['successful_operations'], 0)
        success_rate = (self.integration_stats['successful_operations'] / 
                       max(1, self.integration_stats['total_operations']) * 100)
        self.assertGreater(success_rate, 85)  # At least 85% success rate
    
    def test_concurrent_migration_scenario(self):
        """Test database migration with concurrent operations"""
        print("\n=== Concurrent Migration Scenario Test ===")
        
        # Create JSON files to migrate
        json_files = []
        for i in range(3):
            json_file = os.path.join(self.test_dir, f"migration_data_{i}.json")
            leads_data = []
            
            for j in range(50):
                lead = self._generate_realistic_lead(i, j)
                lead['id'] = str(uuid.uuid4())  # Ensure unique IDs
                leads_data.append(lead)
            
            with open(json_file, 'w') as f:
                json.dump(leads_data, f, indent=2)
            
            json_files.append(json_file)
        
        # Start migration in background
        migration_manager = MigrationManager(self.db_path)
        migration_complete = threading.Event()
        migration_result = {'success': False, 'error': None}
        
        def migration_worker():
            """Background migration worker"""
            try:
                result = migration_manager.migrate_json_files(
                    json_files,
                    create_backup=True,
                    validate_data=True,
                    batch_size=10
                )
                migration_result['success'] = result.success
                migration_result['records_migrated'] = result.records_migrated
                migration_result['duplicates_found'] = result.duplicates_found
                
            except Exception as e:
                migration_result['error'] = str(e)
            finally:
                migration_complete.set()
        
        # Start concurrent operations during migration
        concurrent_ops_active = threading.Event()
        concurrent_ops_active.set()
        
        def concurrent_operations_worker(worker_id: int):
            """Worker performing operations during migration"""
            ops_completed = 0
            
            while concurrent_ops_active.is_set() and not migration_complete.is_set():
                try:
                    # Perform various operations
                    operation_type = random.choice(['read', 'write', 'update'])
                    
                    if operation_type == 'read':
                        # Read operations
                        def read_op():
                            return self.lead_db.get_database_stats()
                        
                        self.access_manager.execute_operation(
                            operation_type="concurrent_read",
                            callback=read_op,
                            priority=OperationPriority.LOW,
                            timeout=10
                        )
                    
                    elif operation_type == 'write':
                        # Write operations
                        lead = self._generate_realistic_lead(worker_id + 100, ops_completed)
                        lead['source'] = 'concurrent_migration_test'
                        
                        def write_op():
                            return self.lead_db.add_lead(lead)
                        
                        self.access_manager.execute_operation(
                            operation_type="concurrent_write",
                            callback=write_op,
                            priority=OperationPriority.NORMAL,
                            timeout=15
                        )
                    
                    elif operation_type == 'update':
                        # Update operations
                        def update_op():
                            with self.lead_db.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT id FROM leads 
                                    WHERE source = 'concurrent_migration_test'
                                    ORDER BY RANDOM() 
                                    LIMIT 1
                                """)
                                row = cursor.fetchone()
                                if row:
                                    return self.lead_db.update_lead(row['id'], {
                                        'title': f'Updated during migration {worker_id}',
                                        'updated_at': datetime.now().isoformat()
                                    })
                                return False
                        
                        self.access_manager.execute_operation(
                            operation_type="concurrent_update",
                            callback=update_op,
                            priority=OperationPriority.NORMAL,
                            timeout=15
                        )
                    
                    ops_completed += 1
                    self._update_stats('successful_operations')
                    
                    # Small delay
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    print(f"Concurrent worker {worker_id} error: {e}")
                    self._update_stats('failed_operations')
            
            print(f"Concurrent worker {worker_id} completed {ops_completed} operations")
        
        # Start migration and concurrent operations
        start_time = time.time()
        
        # Start migration
        migration_thread = threading.Thread(target=migration_worker, name="MigrationWorker")
        migration_thread.start()
        
        # Start concurrent workers
        num_concurrent_workers = 5
        concurrent_threads = []
        
        for i in range(num_concurrent_workers):
            thread = threading.Thread(
                target=concurrent_operations_worker,
                args=(i,),
                name=f"ConcurrentWorker-{i}"
            )
            concurrent_threads.append(thread)
            thread.start()
        
        # Wait for migration to complete
        migration_complete.wait(timeout=120)  # 2 minute timeout
        concurrent_ops_active.clear()
        
        # Wait for concurrent operations to finish
        for thread in concurrent_threads:
            thread.join(timeout=10)
        
        migration_thread.join(timeout=10)
        
        end_time = time.time()
        
        # Analyze results
        db_stats = self.lead_db.get_database_stats()
        access_stats = self.access_manager.get_stats()
        
        print(f"Concurrent migration test completed in {end_time - start_time:.2f} seconds")
        print(f"Migration successful: {migration_result['success']}")
        if migration_result['success']:
            print(f"Records migrated: {migration_result['records_migrated']}")
            print(f"Duplicates found: {migration_result['duplicates_found']}")
        else:
            print(f"Migration error: {migration_result.get('error', 'Unknown error')}")
        
        print(f"Concurrent operations - Success: {self.integration_stats['successful_operations']}, Failed: {self.integration_stats['failed_operations']}")
        print(f"Final database stats: {db_stats}")
        print(f"Deadlocks during migration: {access_stats['concurrent_access_stats']['deadlocks_detected']}")
        
        # Verify data integrity after concurrent migration
        self._verify_integration_data_integrity()
        
        # Assertions
        self.assertTrue(migration_result['success'], f"Migration failed: {migration_result.get('error')}")
        self.assertGreater(self.integration_stats['successful_operations'], 0)
        
        # Clean up JSON files
        for json_file in json_files:
            if os.path.exists(json_file):
                os.remove(json_file)
    
    def test_error_recovery_scenarios(self):
        """Test error recovery and rollback scenarios"""
        print("\n=== Error Recovery Scenarios Test ===")
        
        # Test scenarios that should trigger rollbacks
        num_workers = 10
        operations_per_worker = 20
        
        def error_prone_worker(worker_id: int):
            """Worker that intentionally causes some errors"""
            successful_ops = 0
            failed_ops = 0
            
            for i in range(operations_per_worker):
                try:
                    # Randomly cause different types of errors
                    error_type = random.choice(['none', 'constraint', 'timeout', 'deadlock', 'corruption'])
                    
                    if error_type == 'none' or random.random() < 0.7:  # 70% success rate
                        # Normal operation
                        lead = self._generate_realistic_lead(worker_id, i)
                        lead['source'] = 'error_recovery_test'
                        
                        def normal_operation():
                            return self.lead_db.add_lead(lead)
                        
                        result = self.access_manager.execute_operation(
                            operation_type="error_recovery_normal",
                            callback=normal_operation,
                            priority=OperationPriority.NORMAL,
                            timeout=10
                        )
                        
                        if result:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    elif error_type == 'constraint':
                        # Try to insert duplicate data (should be handled gracefully)
                        duplicate_lead = {
                            'full_name': 'Duplicate Test User',
                            'email': 'duplicate@test.com',
                            'company': 'Duplicate Corp',
                            'linkedin_url': 'https://linkedin.com/in/duplicate',
                            'source': 'error_recovery_test'
                        }
                        
                        def constraint_operation():
                            return self.lead_db.add_lead(duplicate_lead)
                        
                        result = self.access_manager.execute_operation(
                            operation_type="error_recovery_constraint",
                            callback=constraint_operation,
                            priority=OperationPriority.NORMAL,
                            timeout=10
                        )
                        
                        # This should succeed due to duplicate handling
                        if result:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    elif error_type == 'timeout':
                        # Operation that might timeout
                        def timeout_operation():
                            time.sleep(random.uniform(0.5, 2.0))  # Simulate slow operation
                            lead = self._generate_realistic_lead(worker_id + 1000, i)
                            lead['source'] = 'error_recovery_test'
                            return self.lead_db.add_lead(lead)
                        
                        try:
                            result = self.access_manager.execute_operation(
                                operation_type="error_recovery_timeout",
                                callback=timeout_operation,
                                priority=OperationPriority.NORMAL,
                                timeout=1  # Short timeout to trigger timeout errors
                            )
                            
                            if result:
                                successful_ops += 1
                            else:
                                failed_ops += 1
                                
                        except Exception:
                            failed_ops += 1
                    
                    elif error_type == 'deadlock':
                        # Try to create a potential deadlock scenario
                        resource_a = f"resource_a_{worker_id % 3}"
                        resource_b = f"resource_b_{(worker_id + 1) % 3}"
                        
                        def deadlock_operation():
                            with self.access_manager.acquire_resource_lock(resource_a):
                                time.sleep(random.uniform(0.01, 0.05))
                                with self.access_manager.acquire_resource_lock(resource_b, timeout=2):
                                    lead = self._generate_realistic_lead(worker_id + 2000, i)
                                    lead['source'] = 'error_recovery_test'
                                    return self.lead_db.add_lead(lead)
                        
                        try:
                            result = self.access_manager.execute_operation(
                                operation_type="error_recovery_deadlock",
                                callback=deadlock_operation,
                                priority=OperationPriority.NORMAL,
                                timeout=5
                            )
                            
                            if result:
                                successful_ops += 1
                            else:
                                failed_ops += 1
                                
                        except Exception:
                            failed_ops += 1
                    
                    # Small delay between operations
                    time.sleep(random.uniform(0.01, 0.1))
                    
                except Exception as e:
                    failed_ops += 1
                    print(f"Worker {worker_id} operation {i} error: {e}")
            
            self._update_stats('successful_operations', successful_ops)
            self._update_stats('failed_operations', failed_ops)
            
            print(f"Error recovery worker {worker_id}: {successful_ops} success, {failed_ops} failed")
        
        # Start error-prone workers
        start_time = time.time()
        threads = []
        
        for worker_id in range(num_workers):
            thread = threading.Thread(
                target=error_prone_worker,
                args=(worker_id,),
                name=f"ErrorWorker-{worker_id}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)
        
        end_time = time.time()
        
        # Analyze error recovery
        db_stats = self.lead_db.get_database_stats()
        access_stats = self.access_manager.get_stats()
        deadlock_history = self.access_manager.get_deadlock_history()
        
        print(f"Error recovery test completed in {end_time - start_time:.2f} seconds")
        print(f"Successful operations: {self.integration_stats['successful_operations']}")
        print(f"Failed operations: {self.integration_stats['failed_operations']}")
        print(f"Database stats: {db_stats}")
        print(f"Deadlocks detected and resolved: {len(deadlock_history)}")
        print(f"System health after errors: {self.access_manager.health_check()['status']}")
        
        # Verify system recovered properly
        health_check = self.access_manager.health_check()
        pool_health = self.access_manager.connection_pool.health_check()
        
        # Verify data integrity after error scenarios
        self._verify_integration_data_integrity()
        
        # Assertions
        self.assertGreater(self.integration_stats['successful_operations'], 0)
        self.assertEqual(health_check['status'], 'healthy')
        self.assertEqual(pool_health['status'], 'healthy')
    
    def _verify_integration_data_integrity(self):
        """Verify data integrity across the integrated system"""
        try:
            with self.lead_db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for basic database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                
                if integrity_result and integrity_result[0] != 'ok':
                    self._update_stats('data_integrity_issues')
                    print(f"Database integrity issue: {integrity_result[0]}")
                
                # Check for duplicate emails (should be minimal due to duplicate detection)
                cursor.execute("""
                    SELECT email, COUNT(*) as count 
                    FROM leads 
                    WHERE email IS NOT NULL AND email != ''
                    GROUP BY email 
                    HAVING count > 1
                """)
                duplicate_emails = cursor.fetchall()
                
                if duplicate_emails:
                    self._update_stats('data_integrity_issues', len(duplicate_emails))
                    print(f"Found {len(duplicate_emails)} duplicate emails")
                
                # Check for orphaned records or inconsistent states
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM leads 
                    WHERE enriched = 1 AND enriched_at IS NULL
                """)
                inconsistent_enriched = cursor.fetchone()['count']
                
                if inconsistent_enriched > 0:
                    self._update_stats('data_integrity_issues', inconsistent_enriched)
                    print(f"Found {inconsistent_enriched} leads marked as enriched but missing enriched_at")
                
                # Check for sync inconsistencies
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM leads 
                    WHERE airtable_synced = 1 AND airtable_id IS NULL
                """)
                sync_inconsistencies = cursor.fetchone()['count']
                
                if sync_inconsistencies > 0:
                    self._update_stats('data_integrity_issues', sync_inconsistencies)
                    print(f"Found {sync_inconsistencies} leads marked as synced but missing airtable_id")
                
                print(f"Data integrity check completed. Issues found: {self.integration_stats['data_integrity_issues']}")
                
        except Exception as e:
            self._update_stats('data_integrity_issues')
            print(f"Error during data integrity check: {e}")

def run_integration_tests():
    """Run all integration tests"""
    print("Starting Concurrent Access Integration Tests...")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTests(loader.loadTestsFromTestCase(ConcurrentIntegrationTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("Integration Test Summary:")
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
    success = run_integration_tests()
    exit(0 if success else 1)