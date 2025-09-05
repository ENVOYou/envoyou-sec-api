#!/usr/bin/env python3
"""
Master test runner script for authentication system
Runs all testing scripts in sequence with proper error handling
"""

import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path
import argparse

class TestRunner:
    def __init__(self, base_dir: str = "/home/husni/project-permit-api"):
        self.base_dir = Path(base_dir)
        self.results = []
        self.start_time = None

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_script(self, script_path: str, description: str, timeout: int = 300) -> dict:
        """Run a test script and capture results"""
        self.log(f"🚀 Running {description}...")

        script_full_path = self.base_dir / script_path

        if not script_full_path.exists():
            result = {
                "script": script_path,
                "description": description,
                "success": False,
                "error": "Script file not found",
                "duration": 0
            }
            self.results.append(result)
            self.log(f"❌ {description}: Script not found", "ERROR")
            return result

        start_time = time.time()

        try:
            result = subprocess.run(
                [sys.executable, str(script_full_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.base_dir
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            test_result = {
                "script": script_path,
                "description": description,
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }

            self.results.append(test_result)

            if success:
                self.log(f"✅ {description}: PASSED ({duration:.2f}s)")
            else:
                self.log(f"❌ {description}: FAILED ({duration:.2f}s)", "ERROR")
                if result.stderr:
                    self.log(f"Error output: {result.stderr}", "ERROR")

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            result = {
                "script": script_path,
                "description": description,
                "success": False,
                "error": f"Script timed out after {timeout} seconds",
                "duration": duration
            }
            self.results.append(result)
            self.log(f"⏰ {description}: TIMEOUT ({duration:.2f}s)", "ERROR")
            return result

        except Exception as e:
            duration = time.time() - start_time
            result = {
                "script": script_path,
                "description": description,
                "success": False,
                "error": str(e),
                "duration": duration
            }
            self.results.append(result)
            self.log(f"💥 {description}: CRASHED ({duration:.2f}s)", "ERROR")
            return result

    def run_unit_tests(self) -> dict:
        """Run unit tests using pytest"""
        self.log("🧪 Running unit tests...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--json-report", "--json-report-file=test-results.json"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes for tests
                cwd=self.base_dir
            )

            duration = time.time() - time.time()  # Will be set properly in run_script
            success = result.returncode == 0

            # Try to parse test results
            test_summary = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
            try:
                with open(self.base_dir / "test-results.json", 'r') as f:
                    test_data = json.load(f)
                    summary = test_data.get("summary", {})
                    test_summary = {
                        "total": summary.get("num_tests", 0),
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0),
                        "errors": summary.get("errors", 0)
                    }
            except:
                pass

            test_result = {
                "script": "pytest",
                "description": "Unit Tests",
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "test_summary": test_summary
            }

            self.results.append(test_result)

            if success:
                self.log(f"✅ Unit Tests: PASSED ({test_summary['passed']}/{test_summary['total']} tests)")
            else:
                self.log(f"❌ Unit Tests: FAILED ({test_summary['failed']} failed, {test_summary['errors']} errors)", "ERROR")

            return test_result

        except Exception as e:
            result = {
                "script": "pytest",
                "description": "Unit Tests",
                "success": False,
                "error": str(e),
                "duration": 0
            }
            self.results.append(result)
            self.log(f"💥 Unit Tests: CRASHED", "ERROR")
            return result

    def run_all_tests(self, skip_load_tests: bool = False, skip_stress_tests: bool = False) -> bool:
        """Run all test scripts"""
        self.start_time = datetime.now()
        self.log("🎯 Starting Complete Authentication Test Suite")
        self.log("=" * 60)

        # Define test scripts to run
        test_scripts = [
            ("scripts/validate_auth_deployment.py", "Deployment Validation", 120),
            ("scripts/ci_cd_auth_tests.py", "CI/CD Tests", 300),
        ]

        # Add load and stress tests if not skipped
        if not skip_load_tests:
            test_scripts.extend([
                ("scripts/load_test_auth.py", "Load Tests", 180),
            ])

        if not skip_stress_tests:
            test_scripts.extend([
                ("scripts/stress_test_db.py", "Stress Tests", 240),
            ])

        # Run unit tests first
        self.run_unit_tests()

        # Run script-based tests
        for script_path, description, timeout in test_scripts:
            self.run_script(script_path, description, timeout)
            time.sleep(2)  # Brief pause between tests

        # Generate final report
        return self.generate_final_report()

    def generate_final_report(self) -> bool:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests

        # Categorize failures
        critical_failures = []
        non_critical_failures = []

        for result in self.results:
            if not result["success"]:
                if "validation" in result["description"].lower() or "ci/cd" in result["description"].lower():
                    critical_failures.append(result["description"])
                else:
                    non_critical_failures.append(result["description"])

        # Generate report
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "deployment_ready": len(critical_failures) == 0
            },
            "results": self.results,
            "critical_failures": critical_failures,
            "non_critical_failures": non_critical_failures,
            "recommendations": self.generate_recommendations(critical_failures, non_critical_failures)
        }

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.base_dir / f"complete_test_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary
        self.log("\n" + "=" * 60)
        self.log("📊 COMPLETE TEST SUITE SUMMARY:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {failed_tests}")
        self.log(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        self.log(f"   Total Duration: {total_duration:.2f}s")
        self.log(f"   Report Saved: {report_file}")

        if critical_failures:
            self.log("\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                self.log(f"   ❌ {failure}")

        if non_critical_failures:
            self.log("\n⚠️  NON-CRITICAL FAILURES:")
            for failure in non_critical_failures:
                self.log(f"   ⚠️  {failure}")

        recommendations = report["recommendations"]
        if recommendations:
            self.log("\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                self.log(f"   💡 {rec}")

        # Final status
        if report["summary"]["deployment_ready"]:
            self.log("\n✅ DEPLOYMENT READY: All critical tests passed!")
            return True
        else:
            self.log("\n❌ DEPLOYMENT BLOCKED: Critical failures detected!")
            return False

    def generate_recommendations(self, critical: list, non_critical: list) -> list:
        """Generate recommendations based on test results"""
        recommendations = []

        if critical:
            recommendations.append("Fix all critical failures before deployment")
            if "Deployment Validation" in str(critical):
                recommendations.append("Run deployment validation and fix configuration issues")
            if "CI/CD Tests" in str(critical):
                recommendations.append("Fix CI/CD test failures and security issues")

        if non_critical:
            recommendations.append("Address non-critical failures for optimal performance")
            if "Load Tests" in str(non_critical):
                recommendations.append("Optimize performance for production load")
            if "Stress Tests" in str(non_critical):
                recommendations.append("Improve system resilience under stress")

        if not critical and not non_critical:
            recommendations.append("All tests passed - system ready for production")

        return recommendations

def main():
    parser = argparse.ArgumentParser(description="Complete Authentication Test Suite Runner")
    parser.add_argument("--skip-load-tests", action="store_true",
                       help="Skip load testing (can be time-consuming)")
    parser.add_argument("--skip-stress-tests", action="store_true",
                       help="Skip stress testing (can be time-consuming)")
    parser.add_argument("--base-dir", default="/home/husni/project-permit-api",
                       help="Base directory for the project")

    args = parser.parse_args()

    runner = TestRunner(args.base_dir)

    success = runner.run_all_tests(
        skip_load_tests=args.skip_load_tests,
        skip_stress_tests=args.skip_stress_tests
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
