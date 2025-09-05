#!/usr/bin/env python3
"""
CI/CD automated testing script for authentication system
Runs comprehensive tests for deployment validation
"""

import subprocess
import sys
import os
import json
import time
from datetime import datetime
import requests
from typing import Dict, List, Tuple

class CICDAuthTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_command(self, command: str, description: str) -> Tuple[bool, str]:
        """Run shell command and return success status and output"""
        self.log(f"Running: {description}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def test_unit_tests(self) -> bool:
        """Run unit tests"""
        self.log("Running unit tests...")
        success, output = self.run_command(
            "cd /home/husni/project-permit-api && python -m pytest tests/ -v --tb=short",
            "Unit tests"
        )

        self.test_results.append({
            "test": "unit_tests",
            "success": success,
            "output": output,
            "duration": 0
        })

        if success:
            self.log("✅ Unit tests passed")
        else:
            self.log("❌ Unit tests failed")
            self.log(output)

        return success

    def test_auth_tests(self) -> bool:
        """Run authentication-specific tests"""
        self.log("Running authentication tests...")
        success, output = self.run_command(
            "cd /home/husni/project-permit-api && python -m pytest tests/test_auth.py -v --tb=short",
            "Authentication tests"
        )

        self.test_results.append({
            "test": "auth_tests",
            "success": success,
            "output": output,
            "duration": 0
        })

        if success:
            self.log("✅ Authentication tests passed")
        else:
            self.log("❌ Authentication tests failed")
            self.log(output)

        return success

    def test_security_tests(self) -> bool:
        """Run security tests"""
        self.log("Running security tests...")
        success, output = self.run_command(
            "cd /home/husni/project-permit-api && python -m pytest tests/test_security.py -v --tb=short",
            "Security tests"
        )

        self.test_results.append({
            "test": "security_tests",
            "success": success,
            "output": output,
            "duration": 0
        })

        if success:
            self.log("✅ Security tests passed")
        else:
            self.log("❌ Security tests failed")
            self.log(output)

        return success

    def test_api_integration(self) -> bool:
        """Test API integration"""
        self.log("Testing API integration...")

        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=10)
            health_ok = response.status_code == 200

            # Test auth endpoint accessibility
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": "test@example.com", "password": "test"},
                timeout=10
            )
            auth_ok = response.status_code in [401, 422]  # Should fail gracefully

            success = health_ok and auth_ok

            self.test_results.append({
                "test": "api_integration",
                "success": success,
                "output": f"Health: {health_ok}, Auth: {auth_ok}",
                "duration": 0
            })

            if success:
                self.log("✅ API integration tests passed")
            else:
                self.log("❌ API integration tests failed")

            return success

        except Exception as e:
            self.test_results.append({
                "test": "api_integration",
                "success": False,
                "output": str(e),
                "duration": 0
            })
            self.log(f"❌ API integration test failed: {e}")
            return False

    def test_database_migrations(self) -> bool:
        """Test database migrations"""
        self.log("Testing database migrations...")

        # Check if database file exists and is accessible
        db_path = "/home/husni/project-permit-api/app.db"
        if os.path.exists(db_path):
            # Try to connect to database
            success, output = self.run_command(
                "cd /home/husni/project-permit-api && python -c \"import sqlite3; conn = sqlite3.connect('app.db'); conn.close(); print('Database connection successful')\"",
                "Database connection test"
            )
        else:
            success, output = self.run_command(
                "cd /home/husni/project-permit-api && python -c \"from app.models import User; print('Models import successful')\"",
                "Database models test"
            )

        self.test_results.append({
            "test": "database_migrations",
            "success": success,
            "output": output,
            "duration": 0
        })

        if success:
            self.log("✅ Database tests passed")
        else:
            self.log("❌ Database tests failed")
            self.log(output)

        return success

    def test_dependencies(self) -> bool:
        """Test Python dependencies"""
        self.log("Testing Python dependencies...")

        success, output = self.run_command(
            "cd /home/husni/project-permit-api && python -c \"import fastapi, sqlalchemy, jwt, passlib; print('All dependencies imported successfully')\"",
            "Dependencies test"
        )

        self.test_results.append({
            "test": "dependencies",
            "success": success,
            "output": output,
            "duration": 0
        })

        if success:
            self.log("✅ Dependencies test passed")
        else:
            self.log("❌ Dependencies test failed")
            self.log(output)

        return success

    def test_load_performance(self) -> bool:
        """Run basic load performance test"""
        self.log("Running basic load performance test...")

        success, output = self.run_command(
            "cd /home/husni/project-permit-api && python scripts/load_test_auth.py",
            "Load performance test"
        )

        self.test_results.append({
            "test": "load_performance",
            "success": success,
            "output": output,
            "duration": 0
        })

        if success:
            self.log("✅ Load performance test passed")
        else:
            self.log("❌ Load performance test failed")
            self.log(output)

        return success

    def test_security_scan(self) -> bool:
        """Run basic security scan"""
        self.log("Running basic security scan...")

        # Check for common security issues
        checks = []

        # Check if sensitive files are not exposed
        sensitive_files = ['.env', 'secrets.json', 'config.py']
        for file in sensitive_files:
            file_path = f"/home/husni/project-permit-api/{file}"
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if any(secret in content.lower() for secret in ['password', 'secret', 'key']):
                        checks.append(f"Potential sensitive data in {file}")

        # Check file permissions
        db_path = "/home/husni/project-permit-api/app.db"
        if os.path.exists(db_path):
            permissions = oct(os.stat(db_path).st_mode)[-3:]
            if permissions not in ['600', '640', '644']:
                checks.append(f"Database file permissions too open: {permissions}")

        success = len(checks) == 0

        self.test_results.append({
            "test": "security_scan",
            "success": success,
            "output": "\n".join(checks) if checks else "No security issues found",
            "duration": 0
        })

        if success:
            self.log("✅ Security scan passed")
        else:
            self.log("❌ Security scan found issues")
            for check in checks:
                self.log(f"   - {check}")

        return success

    def generate_report(self) -> Dict:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
            },
            "tests": self.test_results,
            "recommendations": []
        }

        # Add recommendations based on failures
        if failed_tests > 0:
            report["recommendations"].append("Review failed tests and fix issues before deployment")
        if not any(t["test"] == "security_scan" and t["success"] for t in self.test_results):
            report["recommendations"].append("Address security scan findings")
        if not any(t["test"] == "load_performance" and t["success"] for t in self.test_results):
            report["recommendations"].append("Investigate performance issues")

        return report

    def save_report(self, report: Dict, filename: str = None):
        """Save test report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/home/husni/project-permit-api/test_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.log(f"Test report saved to: {filename}")

    def run_all_tests(self) -> bool:
        """Run all CI/CD tests"""
        self.start_time = datetime.now()
        self.log("🚀 Starting CI/CD Authentication Tests")
        self.log("=" * 50)

        tests = [
            ("Dependencies", self.test_dependencies),
            ("Database", self.test_database_migrations),
            ("Unit Tests", self.test_unit_tests),
            ("Auth Tests", self.test_auth_tests),
            ("Security Tests", self.test_security_tests),
            ("API Integration", self.test_api_integration),
            ("Load Performance", self.test_load_performance),
            ("Security Scan", self.test_security_scan)
        ]

        overall_success = True

        for test_name, test_func in tests:
            self.log(f"\n📋 Running {test_name}...")
            try:
                success = test_func()
                if not success:
                    overall_success = False
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {e}")
                overall_success = False
                self.test_results.append({
                    "test": test_name.lower().replace(" ", "_"),
                    "success": False,
                    "output": str(e),
                    "duration": 0
                })

        self.end_time = datetime.now()

        # Generate and save report
        report = self.generate_report()
        self.save_report(report)

        # Print summary
        self.log("\n" + "=" * 50)
        self.log("📊 CI/CD Test Summary:")
        self.log(f"   Total Tests: {report['summary']['total_tests']}")
        self.log(f"   Passed: {report['summary']['passed']}")
        self.log(f"   Failed: {report['summary']['failed']}")
        self.log(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        self.log(f"   Duration: {report['summary']['duration']:.2f}s")

        if overall_success:
            self.log("✅ All CI/CD tests passed!")
        else:
            self.log("❌ Some CI/CD tests failed!")
            for rec in report["recommendations"]:
                self.log(f"   💡 {rec}")

        return overall_success

def main():
    """Main CI/CD testing function"""
    tester = CICDAuthTester()

    # Allow custom base URL via environment variable
    base_url = os.getenv("TEST_BASE_URL", "http://localhost:8000")
    tester.base_url = base_url

    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
