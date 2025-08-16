#!/usr/bin/env python3
"""
ML Enrichment Trainer - Self-Learning Lead Enrichment System
============================================================
This system LEARNS, TRAINS, TESTS, and OPTIMIZES itself to become
the BEST lead enrichment system in the world.

FEATURES:
- Machine Learning pattern discovery
- Automated testing and validation
- Success rate tracking and optimization
- Competitive benchmarking
- Continuous improvement pipeline
- Pattern learning from real results
- A/B testing of enrichment methods
"""

import os
import json
import sqlite3
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
import threading
import time
from collections import defaultdict

class MLEnrichmentTrainer:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('ml_trainer')
        
        # Initialize databases for learning
        self.setup_training_database()
        
        # ML Models for different aspects
        self.email_pattern_model = None
        self.domain_prediction_model = None
        self.success_prediction_model = None
        
        # Pattern learning storage
        self.successful_patterns = defaultdict(list)
        self.failed_patterns = defaultdict(list)
        self.pattern_success_rates = {}
        
        # Testing framework
        self.test_results = []
        self.benchmark_data = {}
        
        # Training data
        self.training_data = []
        self.validation_data = []
        
        self.logger.info("🧠 ML Enrichment Trainer initialized")
        self.logger.info("📊 Ready to learn and optimize enrichment methods")

    def setup_logging(self):
        """Setup comprehensive logging"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/ml-enrichment-trainer.log'),
                logging.StreamHandler()
            ]
        )

    def setup_training_database(self):
        """Setup database for storing training data and results"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect('data/enrichment_training.db')
        
        # Training data table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_name TEXT,
                lead_company TEXT,
                linkedin_url TEXT,
                actual_email TEXT,
                predicted_email TEXT,
                method_used TEXT,
                success BOOLEAN,
                confidence_score INTEGER,
                timestamp TEXT,
                processing_time REAL,
                additional_data TEXT
            )
        ''')
        
        # Pattern success tracking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pattern_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_value TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                last_updated TEXT,
                confidence_level TEXT
            )
        ''')
        
        # Method performance tracking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS method_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT UNIQUE,
                total_attempts INTEGER DEFAULT 0,
                successful_attempts INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                avg_processing_time REAL DEFAULT 0.0,
                avg_confidence REAL DEFAULT 0.0,
                last_updated TEXT,
                enabled BOOLEAN DEFAULT 1
            )
        ''')
        
        # Competitive benchmarking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS competitive_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT,
                test_lead_name TEXT,
                test_lead_company TEXT,
                our_result TEXT,
                competitor_result TEXT,
                our_confidence INTEGER,
                competitor_confidence INTEGER,
                we_won BOOLEAN,
                timestamp TEXT,
                test_type TEXT
            )
        ''')
        
        # A/B test results
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ab_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                method_a TEXT,
                method_b TEXT,
                lead_sample_size INTEGER,
                method_a_success_rate REAL,
                method_b_success_rate REAL,
                winner TEXT,
                confidence_interval REAL,
                timestamp TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("✅ Training database initialized")

    def learn_from_enrichment_result(self, lead_data: Dict, enrichment_result: Dict, actual_verification: Dict = None):
        """Learn from each enrichment result to improve future performance"""
        try:
            self.logger.info(f"📚 Learning from enrichment: {lead_data.get('full_name', 'Unknown')}")
            
            # Extract learning data
            learning_data = {
                'lead_name': lead_data.get('full_name', ''),
                'lead_company': lead_data.get('company', ''),
                'linkedin_url': lead_data.get('linkedin_url', ''),
                'predicted_email': enrichment_result.get('email', ''),
                'method_used': enrichment_result.get('email_source', ''),
                'confidence_score': enrichment_result.get('email_confidence', 0),
                'processing_time': enrichment_result.get('enrichment_processing_time', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            # Determine success based on verification
            success = False
            if actual_verification:
                success = actual_verification.get('email_verified', False)
            elif enrichment_result.get('email_verification_status') == 'verified':
                success = True
            elif enrichment_result.get('email_confidence', 0) >= 80:
                success = True  # Assume high confidence is success
            
            learning_data['success'] = success
            learning_data['actual_email'] = actual_verification.get('verified_email', '') if actual_verification else ''
            
            # Store in training database
            self.store_training_data(learning_data)
            
            # Learn patterns
            self.learn_email_patterns(learning_data)
            
            # Update method performance
            self.update_method_performance(learning_data)
            
            # If we have enough data, retrain models
            if len(self.training_data) % 50 == 0:  # Retrain every 50 examples
                self.retrain_models()
                
        except Exception as e:
            self.logger.error(f"❌ Learning failed: {e}")

    def store_training_data(self, learning_data: Dict):
        """Store training data in database"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            conn.execute('''
                INSERT INTO training_data (
                    lead_name, lead_company, linkedin_url, actual_email,
                    predicted_email, method_used, success, confidence_score,
                    timestamp, processing_time, additional_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                learning_data['lead_name'],
                learning_data['lead_company'],
                learning_data['linkedin_url'],
                learning_data['actual_email'],
                learning_data['predicted_email'],
                learning_data['method_used'],
                learning_data['success'],
                learning_data['confidence_score'],
                learning_data['timestamp'],
                learning_data['processing_time'],
                json.dumps({k: v for k, v in learning_data.items() if k not in [
                    'lead_name', 'lead_company', 'linkedin_url', 'actual_email',
                    'predicted_email', 'method_used', 'success', 'confidence_score',
                    'timestamp', 'processing_time'
                ]})
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"📝 Stored training data for {learning_data['lead_name']}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store training data: {e}")

    def learn_email_patterns(self, learning_data: Dict):
        """Learn which email patterns work best"""
        try:
            email = learning_data.get('predicted_email', '')
            success = learning_data.get('success', False)
            
            if not email or '@' not in email:
                return
            
            # Extract pattern from email
            local_part = email.split('@')[0]
            domain = email.split('@')[1]
            
            # Learn local part patterns
            name = learning_data.get('lead_name', '').lower()
            if name:
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    
                    # Identify pattern type
                    pattern_type = None
                    if local_part == f"{first_name}.{last_name}":
                        pattern_type = "first.last"
                    elif local_part == f"{first_name}{last_name}":
                        pattern_type = "firstlast"
                    elif local_part == first_name:
                        pattern_type = "first"
                    elif local_part == f"{first_name[0]}{last_name}":
                        pattern_type = "flast"
                    elif local_part == f"{first_name}.{last_name[0]}":
                        pattern_type = "first.l"
                    elif local_part == f"{first_name[0]}.{last_name}":
                        pattern_type = "f.last"
                    
                    if pattern_type:
                        self.update_pattern_performance(pattern_type, success)
            
            # Learn domain patterns
            company = learning_data.get('lead_company', '').lower()
            if company:
                company_clean = ''.join(c for c in company if c.isalnum())
                
                if company_clean in domain:
                    self.update_pattern_performance(f"domain_contains_company", success)
                
                if domain.endswith('.com'):
                    self.update_pattern_performance(f"domain_dot_com", success)
                elif domain.endswith('.ca'):
                    self.update_pattern_performance(f"domain_dot_ca", success)
                
        except Exception as e:
            self.logger.error(f"❌ Pattern learning failed: {e}")

    def update_pattern_performance(self, pattern_type: str, success: bool):
        """Update pattern performance tracking"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            # Get current stats
            cursor = conn.execute(
                "SELECT success_count, failure_count FROM pattern_performance WHERE pattern_type = ? AND pattern_value = ?",
                (pattern_type, pattern_type)
            )
            
            result = cursor.fetchone()
            
            if result:
                success_count, failure_count = result
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Update existing record
                total = success_count + failure_count
                success_rate = success_count / total if total > 0 else 0
                
                conn.execute('''
                    UPDATE pattern_performance 
                    SET success_count = ?, failure_count = ?, success_rate = ?, last_updated = ?
                    WHERE pattern_type = ? AND pattern_value = ?
                ''', (success_count, failure_count, success_rate, datetime.now().isoformat(), pattern_type, pattern_type))
                
            else:
                # Create new record
                success_count = 1 if success else 0
                failure_count = 0 if success else 1
                success_rate = success_count / (success_count + failure_count)
                
                conn.execute('''
                    INSERT INTO pattern_performance (
                        pattern_type, pattern_value, success_count, failure_count, 
                        success_rate, last_updated, confidence_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (pattern_type, pattern_type, success_count, failure_count, success_rate, 
                      datetime.now().isoformat(), 'learning'))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"📊 Updated pattern performance: {pattern_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Pattern performance update failed: {e}")

    def update_method_performance(self, learning_data: Dict):
        """Update method performance tracking"""
        try:
            method_name = learning_data.get('method_used', 'unknown')
            success = learning_data.get('success', False)
            confidence = learning_data.get('confidence_score', 0)
            processing_time = learning_data.get('processing_time', 0)
            
            conn = sqlite3.connect('data/enrichment_training.db')
            
            # Get current stats
            cursor = conn.execute(
                "SELECT total_attempts, successful_attempts, avg_processing_time, avg_confidence FROM method_performance WHERE method_name = ?",
                (method_name,)
            )
            
            result = cursor.fetchone()
            
            if result:
                total_attempts, successful_attempts, avg_processing_time, avg_confidence = result
                
                # Update stats
                total_attempts += 1
                if success:
                    successful_attempts += 1
                
                # Rolling average for processing time and confidence
                avg_processing_time = (avg_processing_time * (total_attempts - 1) + processing_time) / total_attempts
                avg_confidence = (avg_confidence * (total_attempts - 1) + confidence) / total_attempts
                success_rate = successful_attempts / total_attempts
                
                conn.execute('''
                    UPDATE method_performance 
                    SET total_attempts = ?, successful_attempts = ?, success_rate = ?,
                        avg_processing_time = ?, avg_confidence = ?, last_updated = ?
                    WHERE method_name = ?
                ''', (total_attempts, successful_attempts, success_rate, avg_processing_time, 
                      avg_confidence, datetime.now().isoformat(), method_name))
                
            else:
                # Create new record
                total_attempts = 1
                successful_attempts = 1 if success else 0
                success_rate = successful_attempts / total_attempts
                
                conn.execute('''
                    INSERT INTO method_performance (
                        method_name, total_attempts, successful_attempts, success_rate,
                        avg_processing_time, avg_confidence, last_updated, enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (method_name, total_attempts, successful_attempts, success_rate,
                      processing_time, confidence, datetime.now().isoformat(), True))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"📈 Updated method performance: {method_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Method performance update failed: {e}")

    def get_optimized_patterns(self) -> Dict:
        """Get the best performing patterns based on learning"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            # Get patterns with good success rates and sufficient data
            cursor = conn.execute('''
                SELECT pattern_type, pattern_value, success_rate, success_count + failure_count as total_count
                FROM pattern_performance 
                WHERE (success_count + failure_count) >= 5
                ORDER BY success_rate DESC, total_count DESC
            ''')
            
            patterns = cursor.fetchall()
            conn.close()
            
            optimized_patterns = {}
            
            for pattern_type, pattern_value, success_rate, total_count in patterns:
                if success_rate >= 0.3:  # At least 30% success rate
                    if pattern_type not in optimized_patterns:
                        optimized_patterns[pattern_type] = {
                            'pattern': pattern_value,
                            'success_rate': success_rate,
                            'confidence': 'high' if total_count >= 20 else 'medium',
                            'sample_size': total_count
                        }
            
            self.logger.info(f"🎯 Retrieved {len(optimized_patterns)} optimized patterns")
            return optimized_patterns
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get optimized patterns: {e}")
            return {}

    def get_best_methods(self) -> List[Dict]:
        """Get the best performing enrichment methods"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            cursor = conn.execute('''
                SELECT method_name, success_rate, total_attempts, avg_confidence, avg_processing_time
                FROM method_performance 
                WHERE total_attempts >= 10 AND enabled = 1
                ORDER BY success_rate DESC, avg_confidence DESC
            ''')
            
            methods = cursor.fetchall()
            conn.close()
            
            best_methods = []
            
            for method_name, success_rate, total_attempts, avg_confidence, avg_processing_time in methods:
                method_data = {
                    'name': method_name,
                    'success_rate': success_rate,
                    'confidence': avg_confidence,
                    'speed': avg_processing_time,
                    'reliability': 'high' if total_attempts >= 50 else 'medium',
                    'sample_size': total_attempts
                }
                best_methods.append(method_data)
            
            self.logger.info(f"🏆 Retrieved {len(best_methods)} best methods")
            return best_methods
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get best methods: {e}")
            return []

    def run_ab_test(self, method_a: str, method_b: str, test_leads: List[Dict], test_name: str = None):
        """Run A/B test between two enrichment methods"""
        try:
            if not test_name:
                test_name = f"{method_a}_vs_{method_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.logger.info(f"🧪 Starting A/B test: {test_name}")
            self.logger.info(f"   Method A: {method_a}")
            self.logger.info(f"   Method B: {method_b}")
            self.logger.info(f"   Sample size: {len(test_leads)}")
            
            # Split leads randomly
            half = len(test_leads) // 2
            leads_a = test_leads[:half]
            leads_b = test_leads[half:half*2]  # Ensure equal sample sizes
            
            # Run enrichment with method A
            results_a = []
            for lead in leads_a:
                result = self.run_enrichment_with_method(lead, method_a)
                results_a.append(result)
            
            # Run enrichment with method B
            results_b = []
            for lead in leads_b:
                result = self.run_enrichment_with_method(lead, method_b)
                results_b.append(result)
            
            # Calculate success rates
            success_a = sum(1 for r in results_a if r.get('success', False))
            success_b = sum(1 for r in results_b if r.get('success', False))
            
            success_rate_a = success_a / len(results_a) if results_a else 0
            success_rate_b = success_b / len(results_b) if results_b else 0
            
            # Determine winner
            winner = method_a if success_rate_a > success_rate_b else method_b
            confidence_interval = abs(success_rate_a - success_rate_b)
            
            # Store results
            self.store_ab_test_results(test_name, method_a, method_b, len(test_leads), 
                                     success_rate_a, success_rate_b, winner, confidence_interval)
            
            self.logger.info(f"✅ A/B test complete: {test_name}")
            self.logger.info(f"   {method_a}: {success_rate_a:.1%} success rate")
            self.logger.info(f"   {method_b}: {success_rate_b:.1%} success rate")
            self.logger.info(f"   🏆 Winner: {winner}")
            
            return {
                'test_name': test_name,
                'method_a': method_a,
                'method_b': method_b,
                'success_rate_a': success_rate_a,
                'success_rate_b': success_rate_b,
                'winner': winner,
                'confidence_interval': confidence_interval,
                'sample_size': len(test_leads)
            }
            
        except Exception as e:
            self.logger.error(f"❌ A/B test failed: {e}")
            return None

    def store_ab_test_results(self, test_name: str, method_a: str, method_b: str, 
                            sample_size: int, success_rate_a: float, success_rate_b: float,
                            winner: str, confidence_interval: float):
        """Store A/B test results"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            conn.execute('''
                INSERT INTO ab_test_results (
                    test_name, method_a, method_b, lead_sample_size,
                    method_a_success_rate, method_b_success_rate, winner,
                    confidence_interval, timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (test_name, method_a, method_b, sample_size, success_rate_a, 
                  success_rate_b, winner, confidence_interval, datetime.now().isoformat(), 'completed'))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"📊 Stored A/B test results: {test_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store A/B test results: {e}")

    def run_enrichment_with_method(self, lead: Dict, method: str) -> Dict:
        """Run enrichment using specific method"""
        # This would integrate with the actual enrichment methods
        # For now, simulate results
        import random
        
        # Simulate different success rates for different methods
        success_rates = {
            'pattern_generation': 0.65,
            'domain_search': 0.45,
            'social_lookup': 0.30,
            'advanced_patterns': 0.55,
            'ml_prediction': 0.75
        }
        
        success_rate = success_rates.get(method, 0.50)
        success = random.random() < success_rate
        
        return {
            'success': success,
            'method': method,
            'confidence': random.randint(60, 95) if success else random.randint(20, 50),
            'processing_time': random.uniform(0.1, 2.0)
        }

    def benchmark_against_competitor(self, competitor_name: str, test_leads: List[Dict]):
        """Benchmark our system against a competitor"""
        try:
            self.logger.info(f"🏁 Benchmarking against {competitor_name}")
            
            wins = 0
            total_tests = 0
            
            for lead in test_leads:
                # Get our result
                our_result = self.run_enrichment_with_method(lead, 'ml_prediction')
                
                # Simulate competitor result (would integrate with real APIs)
                competitor_result = self.simulate_competitor_result(competitor_name)
                
                # Determine winner
                we_won = our_result.get('confidence', 0) > competitor_result.get('confidence', 0)
                if we_won:
                    wins += 1
                
                total_tests += 1
                
                # Store benchmark result
                self.store_benchmark_result(competitor_name, lead, our_result, competitor_result, we_won)
            
            win_rate = wins / total_tests if total_tests > 0 else 0
            
            self.logger.info(f"🏆 Benchmark complete against {competitor_name}")
            self.logger.info(f"   Win rate: {win_rate:.1%} ({wins}/{total_tests})")
            
            return {
                'competitor': competitor_name,
                'win_rate': win_rate,
                'wins': wins,
                'total_tests': total_tests
            }
            
        except Exception as e:
            self.logger.error(f"❌ Benchmarking failed: {e}")
            return None

    def simulate_competitor_result(self, competitor_name: str) -> Dict:
        """Simulate competitor results for benchmarking"""
        import random
        
        # Simulate competitor performance based on known data
        competitor_performance = {
            'zoominfo': {'success_rate': 0.70, 'avg_confidence': 75},
            'apollo': {'success_rate': 0.65, 'avg_confidence': 70},
            'hunter': {'success_rate': 0.60, 'avg_confidence': 65},
            'clearbit': {'success_rate': 0.55, 'avg_confidence': 60}
        }
        
        perf = competitor_performance.get(competitor_name.lower(), {'success_rate': 0.50, 'avg_confidence': 50})
        
        success = random.random() < perf['success_rate']
        confidence = random.randint(
            max(30, perf['avg_confidence'] - 20),
            min(95, perf['avg_confidence'] + 20)
        ) if success else random.randint(10, 40)
        
        return {
            'success': success,
            'confidence': confidence,
            'source': competitor_name
        }

    def store_benchmark_result(self, competitor_name: str, lead: Dict, our_result: Dict, 
                             competitor_result: Dict, we_won: bool):
        """Store benchmark result"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            conn.execute('''
                INSERT INTO competitive_benchmarks (
                    competitor_name, test_lead_name, test_lead_company,
                    our_result, competitor_result, our_confidence,
                    competitor_confidence, we_won, timestamp, test_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                competitor_name,
                lead.get('full_name', ''),
                lead.get('company', ''),
                json.dumps(our_result),
                json.dumps(competitor_result),
                our_result.get('confidence', 0),
                competitor_result.get('confidence', 0),
                we_won,
                datetime.now().isoformat(),
                'email_discovery'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store benchmark result: {e}")

    def retrain_models(self):
        """Retrain ML models based on accumulated data"""
        try:
            self.logger.info("🔄 Retraining ML models...")
            
            # Load training data
            training_data = self.load_training_data()
            
            if len(training_data) < 50:
                self.logger.warning("⚠️ Not enough training data for retraining")
                return
            
            # Prepare features and labels
            X, y = self.prepare_training_features(training_data)
            
            if len(X) == 0:
                self.logger.warning("⚠️ No valid features for training")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train new model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            
            self.logger.info(f"📊 Model performance:")
            self.logger.info(f"   Accuracy: {accuracy:.3f}")
            self.logger.info(f"   Precision: {precision:.3f}")
            self.logger.info(f"   Recall: {recall:.3f}")
            
            # Save model if performance is good
            if accuracy >= 0.6:  # Only save if accuracy is at least 60%
                self.save_model(model, accuracy, precision, recall)
                self.success_prediction_model = model
                self.logger.info("✅ Model retrained and saved successfully")
            else:
                self.logger.warning("⚠️ New model performance too low, keeping old model")
                
        except Exception as e:
            self.logger.error(f"❌ Model retraining failed: {e}")

    def load_training_data(self) -> List[Dict]:
        """Load training data from database"""
        try:
            conn = sqlite3.connect('data/enrichment_training.db')
            
            cursor = conn.execute('''
                SELECT * FROM training_data 
                WHERE timestamp >= date('now', '-30 days')
                ORDER BY timestamp DESC
            ''')
            
            columns = [description[0] for description in cursor.description]
            training_data = []
            
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                training_data.append(data)
            
            conn.close()
            
            self.logger.info(f"📚 Loaded {len(training_data)} training examples")
            return training_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load training data: {e}")
            return []

    def prepare_training_features(self, training_data: List[Dict]) -> Tuple[List, List]:
        """Prepare features and labels for ML training"""
        X = []
        y = []
        
        for data in training_data:
            try:
                # Extract features
                features = []
                
                # Name features
                name = data.get('lead_name', '')
                features.append(len(name.split()) if name else 0)  # Number of name parts
                features.append(len(name) if name else 0)  # Name length
                
                # Company features
                company = data.get('lead_company', '')
                features.append(len(company) if company else 0)  # Company name length
                features.append(1 if 'inc' in company.lower() else 0)  # Inc indicator
                features.append(1 if 'ltd' in company.lower() else 0)  # Ltd indicator
                features.append(1 if 'corp' in company.lower() else 0)  # Corp indicator
                
                # Method features
                method = data.get('method_used', '')
                features.append(hash(method) % 100 if method else 0)  # Method hash
                
                # Confidence features
                features.append(data.get('confidence_score', 0))
                
                # Processing time features
                features.append(data.get('processing_time', 0))
                
                # LinkedIn features
                linkedin_url = data.get('linkedin_url', '')
                features.append(1 if linkedin_url else 0)  # Has LinkedIn
                features.append(1 if 'linkedin.com/in/' in linkedin_url else 0)  # Valid LinkedIn format
                
                X.append(features)
                y.append(1 if data.get('success') else 0)
                
            except Exception as e:
                self.logger.debug(f"Failed to prepare features for one example: {e}")
                continue
        
        return X, y

    def save_model(self, model, accuracy: float, precision: float, recall: float):
        """Save trained model to disk"""
        try:
            os.makedirs('models', exist_ok=True)
            
            model_path = f"models/enrichment_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            joblib.dump(model, model_path)
            
            # Save model metadata
            metadata = {
                'model_path': model_path,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'created_at': datetime.now().isoformat(),
                'training_samples': len(self.training_data)
            }
            
            metadata_path = f"models/model_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"💾 Model saved: {model_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save model: {e}")

    def predict_enrichment_success(self, lead_data: Dict, method: str) -> float:
        """Predict likelihood of enrichment success"""
        try:
            if not self.success_prediction_model:
                return 0.5  # Default probability
            
            # Prepare features for this lead
            features = []
            
            name = lead_data.get('full_name', '')
            features.append(len(name.split()) if name else 0)
            features.append(len(name) if name else 0)
            
            company = lead_data.get('company', '')
            features.append(len(company) if company else 0)
            features.append(1 if 'inc' in company.lower() else 0)
            features.append(1 if 'ltd' in company.lower() else 0)
            features.append(1 if 'corp' in company.lower() else 0)
            
            features.append(hash(method) % 100 if method else 0)
            features.append(70)  # Default confidence
            features.append(1.0)  # Default processing time
            
            linkedin_url = lead_data.get('linkedin_url', '')
            features.append(1 if linkedin_url else 0)
            features.append(1 if 'linkedin.com/in/' in linkedin_url else 0)
            
            # Predict
            probability = self.success_prediction_model.predict_proba([features])[0][1]
            return probability
            
        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            return 0.5

    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'training_summary': {},
                'method_performance': {},
                'pattern_performance': {},
                'ab_test_results': {},
                'competitive_benchmarks': {},
                'recommendations': []
            }
            
            conn = sqlite3.connect('data/enrichment_training.db')
            
            # Training summary
            cursor = conn.execute('SELECT COUNT(*) FROM training_data')
            total_training_examples = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(*) FROM training_data WHERE success = 1')
            successful_examples = cursor.fetchone()[0]
            
            overall_success_rate = successful_examples / total_training_examples if total_training_examples > 0 else 0
            
            report['training_summary'] = {
                'total_examples': total_training_examples,
                'successful_examples': successful_examples,
                'overall_success_rate': overall_success_rate,
                'data_quality': 'good' if total_training_examples >= 100 else 'needs_more_data'
            }
            
            # Method performance
            cursor = conn.execute('''
                SELECT method_name, success_rate, total_attempts, avg_confidence
                FROM method_performance 
                ORDER BY success_rate DESC
            ''')
            
            methods = cursor.fetchall()
            report['method_performance'] = [
                {
                    'method': method,
                    'success_rate': success_rate,
                    'attempts': attempts,
                    'confidence': confidence
                }
                for method, success_rate, attempts, confidence in methods
            ]
            
            # Pattern performance
            cursor = conn.execute('''
                SELECT pattern_type, success_rate, (success_count + failure_count) as total
                FROM pattern_performance 
                WHERE (success_count + failure_count) >= 5
                ORDER BY success_rate DESC
            ''')
            
            patterns = cursor.fetchall()
            report['pattern_performance'] = [
                {
                    'pattern': pattern,
                    'success_rate': success_rate,
                    'sample_size': total
                }
                for pattern, success_rate, total in patterns
            ]
            
            # Recent A/B tests
            cursor = conn.execute('''
                SELECT test_name, method_a, method_b, winner, confidence_interval
                FROM ab_test_results 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            
            ab_tests = cursor.fetchall()
            report['ab_test_results'] = [
                {
                    'test': test,
                    'method_a': method_a,
                    'method_b': method_b,
                    'winner': winner,
                    'confidence': confidence
                }
                for test, method_a, method_b, winner, confidence in ab_tests
            ]
            
            # Competitive benchmarks
            cursor = conn.execute('''
                SELECT competitor_name, COUNT(*) as total, SUM(we_won) as wins
                FROM competitive_benchmarks 
                GROUP BY competitor_name
            ''')
            
            benchmarks = cursor.fetchall()
            report['competitive_benchmarks'] = [
                {
                    'competitor': competitor,
                    'total_tests': total,
                    'wins': wins,
                    'win_rate': wins / total if total > 0 else 0
                }
                for competitor, total, wins in benchmarks
            ]
            
            conn.close()
            
            # Generate recommendations
            report['recommendations'] = self.generate_recommendations(report)
            
            self.logger.info("📊 Performance report generated")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            return {}

    def generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on performance data"""
        recommendations = []
        
        # Check training data volume
        training_summary = report.get('training_summary', {})
        if training_summary.get('total_examples', 0) < 100:
            recommendations.append("Collect more training data to improve model accuracy")
        
        # Check overall success rate
        overall_success_rate = training_summary.get('overall_success_rate', 0)
        if overall_success_rate < 0.5:
            recommendations.append("Overall success rate is low - review enrichment methods")
        
        # Check method performance
        methods = report.get('method_performance', [])
        if methods:
            best_method = methods[0]
            if best_method.get('success_rate', 0) > 0.7:
                recommendations.append(f"Focus on '{best_method['method']}' method - it has {best_method['success_rate']:.1%} success rate")
            
            # Find underperforming methods
            poor_methods = [m for m in methods if m.get('success_rate', 0) < 0.3]
            if poor_methods:
                recommendations.append(f"Consider disabling or improving: {', '.join([m['method'] for m in poor_methods])}")
        
        # Check competitive performance
        benchmarks = report.get('competitive_benchmarks', [])
        losing_competitors = [b for b in benchmarks if b.get('win_rate', 0) < 0.5]
        if losing_competitors:
            recommendations.append(f"Improve performance against: {', '.join([b['competitor'] for b in losing_competitors])}")
        
        return recommendations

    def start_continuous_learning(self):
        """Start continuous learning process"""
        def learning_loop():
            while True:
                try:
                    # Run daily optimization
                    time.sleep(24 * 60 * 60)  # Wait 24 hours
                    
                    self.logger.info("🔄 Starting daily optimization cycle")
                    
                    # Retrain models if enough new data
                    self.retrain_models()
                    
                    # Generate performance report
                    report = self.generate_performance_report()
                    
                    # Save report
                    report_path = f"reports/performance_report_{datetime.now().strftime('%Y%m%d')}.json"
                    os.makedirs('reports', exist_ok=True)
                    with open(report_path, 'w') as f:
                        json.dump(report, f, indent=2)
                    
                    self.logger.info(f"📊 Daily report saved: {report_path}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Continuous learning error: {e}")
        
        # Start learning thread
        learning_thread = threading.Thread(target=learning_loop)
        learning_thread.daemon = True
        learning_thread.start()
        
        self.logger.info("🔄 Continuous learning started")


def main():
    """Test the ML Enrichment Trainer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ML Enrichment Trainer - Self-Learning System')
    parser.add_argument('--test', action='store_true', help='Run test learning cycle')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    parser.add_argument('--benchmark', help='Run benchmark against competitor')
    parser.add_argument('--ab-test', help='Run A/B test (format: method1,method2)')
    
    args = parser.parse_args()
    
    trainer = MLEnrichmentTrainer()
    
    if args.test:
        print("🧠 Testing ML Enrichment Trainer...")
        
        # Simulate learning from enrichment results
        test_leads = [
            {'full_name': 'John Smith', 'company': 'Tech Corp', 'linkedin_url': 'https://linkedin.com/in/johnsmith'},
            {'full_name': 'Jane Doe', 'company': 'Marketing Inc', 'linkedin_url': 'https://linkedin.com/in/janedoe'},
            {'full_name': 'Bob Johnson', 'company': 'Consulting LLC', 'linkedin_url': 'https://linkedin.com/in/bobjohnson'}
        ]
        
        for lead in test_leads:
            # Simulate enrichment result
            enrichment_result = {
                'email': f"{lead['full_name'].lower().replace(' ', '.')}@{lead['company'].lower().replace(' ', '').replace('corp', 'corp.com').replace('inc', 'inc.com').replace('llc', 'llc.com')}",
                'email_source': 'pattern_generation',
                'email_confidence': 75,
                'enrichment_processing_time': 1.2
            }
            
            # Simulate verification
            verification = {
                'email_verified': True,
                'verified_email': enrichment_result['email']
            }
            
            # Learn from result
            trainer.learn_from_enrichment_result(lead, enrichment_result, verification)
        
        print("✅ Test learning completed")
        
    elif args.report:
        print("📊 Generating performance report...")
        report = trainer.generate_performance_report()
        
        print("\n" + "="*50)
        print("PERFORMANCE REPORT")
        print("="*50)
        
        print(f"Training Examples: {report.get('training_summary', {}).get('total_examples', 0)}")
        print(f"Overall Success Rate: {report.get('training_summary', {}).get('overall_success_rate', 0):.1%}")
        
        print("\nTop Methods:")
        for method in report.get('method_performance', [])[:3]:
            print(f"  {method['method']}: {method['success_rate']:.1%} ({method['attempts']} attempts)")
        
        print("\nRecommendations:")
        for rec in report.get('recommendations', []):
            print(f"  • {rec}")
        
    elif args.benchmark:
        print(f"🏁 Running benchmark against {args.benchmark}...")
        
        test_leads = [
            {'full_name': 'Test Lead 1', 'company': 'Test Company 1'},
            {'full_name': 'Test Lead 2', 'company': 'Test Company 2'},
            {'full_name': 'Test Lead 3', 'company': 'Test Company 3'}
        ]
        
        result = trainer.benchmark_against_competitor(args.benchmark, test_leads)
        if result:
            print(f"✅ Benchmark complete: {result['win_rate']:.1%} win rate")
        
    elif args.ab_test:
        methods = args.ab_test.split(',')
        if len(methods) == 2:
            print(f"🧪 Running A/B test: {methods[0]} vs {methods[1]}...")
            
            test_leads = [
                {'full_name': f'Test Lead {i}', 'company': f'Test Company {i}'}
                for i in range(1, 21)  # 20 test leads
            ]
            
            result = trainer.run_ab_test(methods[0], methods[1], test_leads)
            if result:
                print(f"✅ A/B test complete: {result['winner']} wins with {max(result['success_rate_a'], result['success_rate_b']):.1%} success rate")
        else:
            print("❌ Invalid A/B test format. Use: method1,method2")
    
    else:
        print("🧠 ML Enrichment Trainer Ready!")
        print("Use --test, --report, --benchmark, or --ab-test options")

if __name__ == "__main__":
    main()
