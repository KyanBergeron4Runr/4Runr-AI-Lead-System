#!/usr/bin/env python3
"""
4Runr AI Lead System - Code Organization Script
Organizes scattered code files into logical structure and identifies duplicates
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import hashlib
import logging

class CodeOrganizer:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.organized_dir = self.root_dir / "organized_system"
        self.analysis_dir = self.root_dir / "code_analysis"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.root_dir / "logs" / "code_organization.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Define organized structure
        self.organized_structure = {
            "core": {
                "database": "Database layer and connection management",
                "config": "Configuration management",
                "utils": "Shared utilities and helpers",
                "api": "API interfaces and clients"
            },
            "modules": {
                "brain": "AI learning and decision making",
                "scraper": "Lead discovery and data collection",
                "outreach": "Outreach automation and messaging",
                "enrichment": "Data enrichment and validation"
            },
            "services": {
                "automation": "Automated processes and scheduling",
                "monitoring": "System monitoring and health checks",
                "backup": "Backup and recovery services"
            },
            "deployment": "Deployment tools and scripts",
            "docs": "Documentation",
            "tests": "Test suite",
            "data": "Data storage"
        }
        
    def log(self, message: str, level: str = "info"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if level == "error":
            self.logger.error(formatted_message)
        elif level == "warning":
            self.logger.warning(formatted_message)
        else:
            self.logger.info(formatted_message)
            
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the current codebase structure"""
        self.log("🔍 Analyzing current codebase structure...")
        
        analysis = {
            "total_files": 0,
            "total_lines": 0,
            "file_types": {},
            "directories": {},
            "duplicate_files": [],
            "large_files": [],
            "test_files": [],
            "configuration_files": [],
            "documentation_files": []
        }
        
        # Analyze all Python files
        python_files = list(self.root_dir.rglob("*.py"))
        analysis["total_files"] = len(python_files)
        
        for file_path in python_files:
            try:
                # Skip certain directories
                if any(skip_dir in str(file_path) for skip_dir in [".git", "__pycache__", ".venv", ".kiro"]):
                    continue
                    
                # Get file info
                file_size = file_path.stat().st_size
                relative_path = file_path.relative_to(self.root_dir)
                
                # Count lines
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    line_count = len(lines)
                    analysis["total_lines"] += line_count
                
                # Categorize files
                if "test" in file_path.name.lower():
                    analysis["test_files"].append({
                        "path": str(relative_path),
                        "size": file_size,
                        "lines": line_count
                    })
                elif file_path.name in [".env", "config.py", "settings.py"]:
                    analysis["configuration_files"].append({
                        "path": str(relative_path),
                        "size": file_size,
                        "lines": line_count
                    })
                elif file_path.suffix in [".md", ".txt", ".rst"]:
                    analysis["documentation_files"].append({
                        "path": str(relative_path),
                        "size": file_size,
                        "lines": line_count
                    })
                
                # Track large files
                if file_size > 50000:  # 50KB
                    analysis["large_files"].append({
                        "path": str(relative_path),
                        "size": file_size,
                        "lines": line_count
                    })
                    
            except Exception as e:
                self.log(f"Error analyzing {file_path}: {str(e)}", "warning")
                
        # Analyze directories
        for item in self.root_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                analysis["directories"][item.name] = {
                    "type": "directory",
                    "size": self.get_directory_size(item),
                    "files": len(list(item.rglob("*.py")))
                }
                
        self.log(f"✅ Analysis complete: {analysis['total_files']} files, {analysis['total_lines']} lines")
        return analysis
        
    def get_directory_size(self, directory: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size
        
    def find_duplicate_functionality(self) -> List[Dict[str, Any]]:
        """Find duplicate functionality across the codebase"""
        self.log("🔍 Finding duplicate functionality...")
        
        duplicates = []
        
        # Common patterns that indicate duplicate functionality
        duplicate_patterns = [
            "database_connection",
            "lead_database", 
            "airtable_client",
            "data_cleaner",
            "message_generator",
            "email_sender",
            "website_scraper",
            "enricher",
            "config_manager",
            "logger",
            "backup",
            "monitoring"
        ]
        
        for pattern in duplicate_patterns:
            matching_files = list(self.root_dir.rglob(f"*{pattern}*.py"))
            if len(matching_files) > 1:
                duplicates.append({
                    "pattern": pattern,
                    "files": [str(f.relative_to(self.root_dir)) for f in matching_files],
                    "count": len(matching_files)
                })
                
        self.log(f"✅ Found {len(duplicates)} duplicate patterns")
        return duplicates
        
    def create_organized_structure(self):
        """Create the organized directory structure"""
        self.log("🏗️ Creating organized directory structure...")
        
        # Create main organized directory
        self.organized_dir.mkdir(exist_ok=True)
        
        # Create structure
        for main_dir, sub_dirs in self.organized_structure.items():
            if isinstance(sub_dirs, dict):
                # Create main directory
                main_path = self.organized_dir / main_dir
                main_path.mkdir(exist_ok=True)
                
                # Create subdirectories
                for sub_dir, description in sub_dirs.items():
                    sub_path = main_path / sub_dir
                    sub_path.mkdir(exist_ok=True)
                    
                    # Create README for subdirectory
                    readme_path = sub_path / "README.md"
                    if not readme_path.exists():
                        with open(readme_path, 'w') as f:
                            f.write(f"# {sub_dir.title()}\n\n{description}\n")
            else:
                # Simple directory
                dir_path = self.organized_dir / main_dir
                dir_path.mkdir(exist_ok=True)
                
        self.log(f"✅ Organized structure created: {self.organized_dir}")
        
    def categorize_files(self) -> Dict[str, List[str]]:
        """Categorize files into organized structure"""
        self.log("📂 Categorizing files...")
        
        categories = {
            "core/database": [],
            "core/config": [],
            "core/utils": [],
            "core/api": [],
            "modules/brain": [],
            "modules/scraper": [],
            "modules/outreach": [],
            "modules/enrichment": [],
            "services/automation": [],
            "services/monitoring": [],
            "services/backup": [],
            "deployment": [],
            "docs": [],
            "tests": [],
            "data": []
        }
        
        # File categorization rules
        categorization_rules = {
            "core/database": [
                "database", "db_", "lead_database", "connection", "migration"
            ],
            "core/config": [
                "config", "settings", ".env", "configuration"
            ],
            "core/utils": [
                "utils", "helpers", "common", "shared"
            ],
            "core/api": [
                "api", "client", "airtable", "openai", "serpapi"
            ],
            "modules/brain": [
                "brain", "ai_", "campaign_brain", "learning"
            ],
            "modules/scraper": [
                "scraper", "lead_finder", "serpapi_scraper"
            ],
            "modules/outreach": [
                "outreach", "email", "message", "campaign"
            ],
            "modules/enrichment": [
                "enricher", "enrichment", "validation", "cleaner"
            ],
            "services/automation": [
                "automation", "scheduler", "cron", "daily"
            ],
            "services/monitoring": [
                "monitoring", "health", "dashboard", "status"
            ],
            "services/backup": [
                "backup", "recovery", "restore"
            ],
            "deployment": [
                "deploy", "ec2", "docker", "build"
            ],
            "tests": [
                "test_", "_test", "tests"
            ],
            "docs": [
                ".md", ".txt", ".rst", "README", "documentation"
            ]
        }
        
        # Categorize Python files
        python_files = list(self.root_dir.rglob("*.py"))
        
        for file_path in python_files:
            if any(skip_dir in str(file_path) for skip_dir in [".git", "__pycache__", ".venv", ".kiro"]):
                continue
                
            relative_path = str(file_path.relative_to(self.root_dir))
            file_name = file_path.name.lower()
            
            # Find matching category
            categorized = False
            for category, patterns in categorization_rules.items():
                if any(pattern in file_name or pattern in relative_path.lower() for pattern in patterns):
                    categories[category].append(relative_path)
                    categorized = True
                    break
                    
            # Default to core/utils if not categorized
            if not categorized:
                categories["core/utils"].append(relative_path)
                
        # Categorize documentation files
        doc_files = list(self.root_dir.rglob("*.md")) + list(self.root_dir.rglob("*.txt"))
        for file_path in doc_files:
            if any(skip_dir in str(file_path) for skip_dir in [".git", "__pycache__", ".venv", ".kiro"]):
                continue
            categories["docs"].append(str(file_path.relative_to(self.root_dir)))
            
        self.log(f"✅ Categorized {sum(len(files) for files in categories.values())} files")
        return categories
        
    def create_migration_plan(self, categories: Dict[str, List[str]], duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a migration plan for organizing the code"""
        self.log("📋 Creating migration plan...")
        
        migration_plan = {
            "timestamp": datetime.now().isoformat(),
            "total_files_to_move": sum(len(files) for files in categories.values()),
            "duplicate_patterns": len(duplicates),
            "categories": categories,
            "duplicates": duplicates,
            "steps": [
                "1. Create organized directory structure",
                "2. Move files to appropriate categories",
                "3. Consolidate duplicate functionality",
                "4. Update import statements",
                "5. Create unified configuration",
                "6. Update documentation"
            ],
            "estimated_time": "2-3 days",
            "risks": [
                "Import path changes may break existing code",
                "Some files may not fit clean categories",
                "Duplicate consolidation requires careful testing"
            ]
        }
        
        return migration_plan
        
    def generate_consolidation_recommendations(self, duplicates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations for consolidating duplicate functionality"""
        self.log("💡 Generating consolidation recommendations...")
        
        recommendations = []
        
        for duplicate in duplicates:
            pattern = duplicate["pattern"]
            files = duplicate["files"]
            
            recommendation = {
                "pattern": pattern,
                "files": files,
                "recommendation": self.get_consolidation_recommendation(pattern, files),
                "priority": self.get_consolidation_priority(pattern),
                "estimated_effort": "medium"
            }
            
            recommendations.append(recommendation)
            
        return recommendations
        
    def get_consolidation_recommendation(self, pattern: str, files: List[str]) -> str:
        """Get specific recommendation for consolidating a pattern"""
        recommendations = {
            "database_connection": "Create unified database connection manager in core/database",
            "lead_database": "Consolidate into single lead database interface in core/database",
            "airtable_client": "Create unified Airtable client in core/api",
            "data_cleaner": "Consolidate data cleaning logic into modules/enrichment",
            "message_generator": "Unify message generation in modules/outreach",
            "email_sender": "Create single email service in modules/outreach",
            "website_scraper": "Consolidate scraping logic in modules/scraper",
            "enricher": "Unify enrichment logic in modules/enrichment",
            "config_manager": "Create centralized configuration in core/config",
            "logger": "Implement unified logging system in core/utils",
            "backup": "Create centralized backup service in services/backup",
            "monitoring": "Unify monitoring in services/monitoring"
        }
        
        return recommendations.get(pattern, f"Review and consolidate {pattern} functionality")
        
    def get_consolidation_priority(self, pattern: str) -> str:
        """Get priority level for consolidation"""
        high_priority = ["database_connection", "lead_database", "config_manager", "logger"]
        medium_priority = ["airtable_client", "data_cleaner", "message_generator", "email_sender"]
        
        if pattern in high_priority:
            return "high"
        elif pattern in medium_priority:
            return "medium"
        else:
            return "low"
            
    def create_organization_report(self, analysis: Dict[str, Any], categories: Dict[str, List[str]], 
                                 duplicates: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive organization report"""
        self.log("📊 Creating organization report...")
        
        report = {
            "organization_date": datetime.now().isoformat(),
            "codebase_analysis": analysis,
            "file_categories": categories,
            "duplicate_patterns": duplicates,
            "consolidation_recommendations": recommendations,
            "organized_structure": self.organized_structure,
            "summary": {
                "total_files": analysis["total_files"],
                "total_lines": analysis["total_lines"],
                "duplicate_patterns": len(duplicates),
                "categories_created": len(categories),
                "high_priority_consolidations": len([r for r in recommendations if r["priority"] == "high"])
            }
        }
        
        report_path = self.analysis_dir / "code_organization_report.json"
        self.analysis_dir.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"✅ Organization report created: {report_path}")
        return report
        
    def run_organization_analysis(self):
        """Run the complete code organization analysis"""
        self.log("🚀 Starting code organization analysis...")
        
        try:
            # Step 1: Analyze current codebase
            analysis = self.analyze_codebase()
            
            # Step 2: Find duplicate functionality
            duplicates = self.find_duplicate_functionality()
            
            # Step 3: Create organized structure
            self.create_organized_structure()
            
            # Step 4: Categorize files
            categories = self.categorize_files()
            
            # Step 5: Generate consolidation recommendations
            recommendations = self.generate_consolidation_recommendations(duplicates)
            
            # Step 6: Create migration plan
            migration_plan = self.create_migration_plan(categories, duplicates)
            
            # Step 7: Create comprehensive report
            report = self.create_organization_report(analysis, categories, duplicates, recommendations)
            
            self.log("🎉 Code organization analysis completed successfully!")
            self.log(f"📊 Summary:")
            self.log(f"   - Total files analyzed: {analysis['total_files']}")
            self.log(f"   - Total lines of code: {analysis['total_lines']}")
            self.log(f"   - Duplicate patterns found: {len(duplicates)}")
            self.log(f"   - File categories created: {len(categories)}")
            self.log(f"   - High priority consolidations: {len([r for r in recommendations if r['priority'] == 'high'])}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Organization analysis failed: {str(e)}", "error")
            return False

def main():
    """Main function to run code organization analysis"""
    organizer = CodeOrganizer()
    success = organizer.run_organization_analysis()
    
    if success:
        print("\n🎉 Code organization analysis completed successfully!")
        print("📋 Next steps:")
        print("   1. Review the organization report")
        print("   2. Prioritize consolidation efforts")
        print("   3. Create migration scripts for file moves")
        print("   4. Update import statements systematically")
        print("   5. Test functionality after reorganization")
    else:
        print("\n❌ Code organization analysis failed. Check logs for details.")

if __name__ == "__main__":
    main()
