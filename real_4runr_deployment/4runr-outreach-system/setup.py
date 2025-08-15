#!/usr/bin/env python3
"""
Automated Setup Script for 4Runr Outreach System

This script helps new developers get the system up and running quickly
by automating the setup process and running verification tests.
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Tuple, List

class SetupManager:
    """Manages the automated setup process."""
    
    def __init__(self):
        """Initialize the setup manager."""
        self.project_root = Path(__file__).parent
        self.setup_steps = []
    
    def run_setup(self) -> bool:
        """Run the complete setup process."""
        print("🚀 4Runr Outreach System Setup")
        print("=" * 40)
        print("This script will help you set up the system for development.")
        print()
        
        steps = [
            ("Check Python Version", self.check_python_version),
            ("Check Environment File", self.check_env_file),
            ("Install Dependencies", self.install_dependencies),
            ("Verify Dependencies", self.verify_dependencies),
            ("Test Knowledge Base", self.test_knowledge_base),
            ("Test System Integration", self.test_system_integration),
            ("Show Next Steps", self.show_next_steps)
        ]
        
        all_success = True
        
        for step_name, step_func in steps:
            print(f"🔧 {step_name}...")
            try:
                success, message = step_func()
                status = "✅" if success else "❌"
                print(f"   {status} {message}")
                
                if not success:
                    all_success = False
                    if step_name in ["Install Dependencies", "Verify Dependencies"]:
                        print("   ⚠️  This is a critical step. Setup cannot continue.")
                        break
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                all_success = False
                break
            
            print()
        
        if all_success:
            print("🎉 Setup completed successfully!")
            print("   The system is ready for use.")
        else:
            print("⚠️  Setup completed with issues.")
            print("   Please review the errors above and fix them manually.")
        
        return all_success
    
    def check_python_version(self) -> Tuple[bool, str]:
        """Check if Python version is compatible."""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro} (compatible)"
        else:
            return False, f"Python {version.major}.{version.minor}.{version.micro} (requires Python 3.8+)"
    
    def check_env_file(self) -> Tuple[bool, str]:
        """Check if .env file exists, create from example if not."""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            return True, ".env file already exists"
        elif env_example.exists():
            try:
                # Copy .env.example to .env
                with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                    dst.write(src.read())
                return True, ".env file created from .env.example (please configure API keys)"
            except Exception as e:
                return False, f"Failed to create .env file: {e}"
        else:
            return False, ".env.example file not found"
    
    def install_dependencies(self) -> Tuple[bool, str]:
        """Install Python dependencies from requirements.txt."""
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            return False, "requirements.txt not found"
        
        try:
            # First try to check if dependencies are already installed
            result_check = subprocess.run([
                sys.executable, "-m", "pip", "check"
            ], capture_output=True, text=True, timeout=30)
            
            # Try to install dependencies
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return True, "All dependencies installed successfully"
            else:
                # If installation failed, check if it's because they're already installed
                if "already satisfied" in result.stdout.lower():
                    return True, "Dependencies already installed"
                else:
                    # Try to continue anyway and let the verification step catch issues
                    return True, f"Installation completed with warnings (will verify in next step)"
                
        except subprocess.TimeoutExpired:
            return False, "Installation timed out (network issues?)"
        except Exception as e:
            return False, f"Installation failed: {e}"
    
    def verify_dependencies(self) -> Tuple[bool, str]:
        """Verify that all dependencies can be imported."""
        try:
            # Run the dependency test script
            test_script = self.project_root / "test_dependencies.py"
            if not test_script.exists():
                return False, "test_dependencies.py not found"
            
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True, "All dependencies verified successfully"
            else:
                return False, f"Dependency verification failed: {result.stderr[:200]}"
                
        except Exception as e:
            return False, f"Dependency verification error: {e}"
    
    def test_knowledge_base(self) -> Tuple[bool, str]:
        """Test the knowledge base configuration."""
        try:
            # Run the knowledge base verification script
            test_script = self.project_root / "verify_knowledge_base_fix.py"
            if not test_script.exists():
                return False, "verify_knowledge_base_fix.py not found"
            
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, "Knowledge base verified successfully"
            else:
                return False, "Knowledge base verification failed"
                
        except Exception as e:
            return False, f"Knowledge base test error: {e}"
    
    def test_system_integration(self) -> Tuple[bool, str]:
        """Test the complete system integration."""
        try:
            # Run the engager agent in dry-run mode
            result = subprocess.run([
                sys.executable, "-m", "engager.enhanced_engager_agent", 
                "--dry-run", "--limit", "1"
            ], capture_output=True, text=True, timeout=60)
            
            output = result.stdout + result.stderr
            
            # Check for success indicators
            if "4Runr knowledge base loaded successfully" in output:
                return True, "System integration test passed"
            else:
                return False, "System integration test failed (check API keys in .env)"
                
        except Exception as e:
            return False, f"System integration test error: {e}"
    
    def show_next_steps(self) -> Tuple[bool, str]:
        """Show next steps for the user."""
        next_steps = """
Next Steps:
1. Configure API keys in .env file:
   - AIRTABLE_API_KEY (get from https://airtable.com/account)
   - OPENAI_API_KEY (get from https://platform.openai.com/api-keys)
   
2. Test the system:
   python -m engager.enhanced_engager_agent --dry-run --limit 1
   
3. Read SETUP.md for detailed usage instructions
        """
        print(next_steps)
        return True, "Setup guide displayed"

def main():
    """Main setup function."""
    setup_manager = SetupManager()
    success = setup_manager.run_setup()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)