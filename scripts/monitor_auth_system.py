#!/usr/bin/env python3
"""
Monitoring and alerting script for authentication system
Monitors API health, security events, and performance metrics
"""

import asyncio
import aiohttp
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/husni/project-permit-api/logs/auth_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuthSystemMonitor:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.alerts_sent = set()
        self.metrics_history = []
        self.alert_thresholds = {
            "response_time": 5.0,  # seconds
            "error_rate": 0.05,    # 5%
            "cpu_usage": 80.0,     # percentage
            "memory_usage": 80.0,  # percentage
            "failed_logins": 10,   # per minute
            "rate_limit_hits": 5   # per minute
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def send_alert_email(self, subject: str, message: str):
        """Send alert email notification"""
        try:
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            alert_email = os.getenv("ALERT_EMAIL", "admin@example.com")

            if not all([smtp_username, smtp_password]):
                logger.warning("SMTP credentials not configured, skipping email alert")
                return

            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = alert_email
            msg['Subject'] = f"🚨 Auth System Alert: {subject}"

            body = f"""
Authentication System Alert
Time: {datetime.now().isoformat()}
Subject: {subject}

{message}

This is an automated alert from the authentication system monitor.
Please investigate immediately.
            """
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Alert email sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")

    async def check_api_health(self) -> Dict:
        """Check basic API health and response times"""
        endpoints = [
            "/health",
            "/auth/login",
            "/api/permits/search"
        ]

        results = {}
        for endpoint in endpoints:
            start_time = time.time()
            try:
                async with self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    results[endpoint] = {
                        "status": response.status,
                        "response_time": response_time,
                        "healthy": response.status in [200, 201, 404]  # 404 is ok for some endpoints
                    }
            except Exception as e:
                response_time = time.time() - start_time
                results[endpoint] = {
                    "status": 0,
                    "response_time": response_time,
                    "healthy": False,
                    "error": str(e)
                }

        return results

    async def check_auth_endpoints(self) -> Dict:
        """Check authentication-specific endpoints and security"""
        auth_results = {}

        # Test login with invalid credentials (should fail gracefully)
        try:
            async with self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": "invalid@example.com", "password": "wrong"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                auth_results["login_invalid"] = {
                    "status": response.status,
                    "response_time": time.time() - time.time(),
                    "secure": response.status in [401, 422]  # Should return auth error, not server error
                }
        except Exception as e:
            auth_results["login_invalid"] = {
                "status": 0,
                "error": str(e),
                "secure": False
            }

        # Test registration rate limiting
        rate_limit_results = []
        for i in range(5):
            try:
                async with self.session.post(
                    f"{self.base_url}/auth/register",
                    json={
                        "email": f"ratetest_{int(time.time())}_{i}@example.com",
                        "password": "TestPass123!",
                        "name": "Rate Test User"
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    rate_limit_results.append({
                        "attempt": i+1,
                        "status": response.status,
                        "rate_limited": response.status == 429
                    })
            except Exception as e:
                rate_limit_results.append({
                    "attempt": i+1,
                    "status": 0,
                    "error": str(e)
                })

        auth_results["rate_limiting"] = rate_limit_results

        return auth_results

    async def check_security_headers(self) -> Dict:
        """Check for proper security headers"""
        try:
            async with self.session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                headers = dict(response.headers)

                security_checks = {
                    "x_content_type_options": "nosniff" in headers.get("X-Content-Type-Options", "").lower(),
                    "x_frame_options": bool(headers.get("X-Frame-Options")),
                    "x_xss_protection": bool(headers.get("X-XSS-Protection")),
                    "content_security_policy": bool(headers.get("Content-Security-Policy")),
                    "strict_transport_security": bool(headers.get("Strict-Transport-Security")),
                    "server_header_hidden": "Server" not in headers
                }

                return {
                    "headers_present": security_checks,
                    "all_secure": all(security_checks.values())
                }
        except Exception as e:
            return {
                "error": str(e),
                "all_secure": False
            }

    async def monitor_logs_for_security_events(self) -> Dict:
        """Monitor application logs for security events"""
        try:
            log_file = "/home/husni/project-permit-api/logs/app.log"
            if not os.path.exists(log_file):
                return {"error": "Log file not found"}

            # Read recent log entries
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines

            security_events = {
                "failed_logins": 0,
                "rate_limit_hits": 0,
                "suspicious_requests": 0,
                "auth_errors": 0
            }

            for line in lines:
                line_lower = line.lower()
                if "failed login" in line_lower or "invalid credentials" in line_lower:
                    security_events["failed_logins"] += 1
                if "rate limit" in line_lower or "too many requests" in line_lower:
                    security_events["rate_limit_hits"] += 1
                if "suspicious" in line_lower or "attack" in line_lower:
                    security_events["suspicious_requests"] += 1
                if "authentication error" in line_lower or "auth failed" in line_lower:
                    security_events["auth_errors"] += 1

            return security_events

        except Exception as e:
            return {"error": str(e)}

    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")

        # Collect all metrics
        health_metrics = await self.check_api_health()
        auth_metrics = await self.check_auth_endpoints()
        security_headers = await self.check_security_headers()
        security_events = await self.monitor_logs_for_security_events()

        # Store metrics history
        metrics_snapshot = {
            "timestamp": datetime.now().isoformat(),
            "health": health_metrics,
            "auth": auth_metrics,
            "security_headers": security_headers,
            "security_events": security_events
        }
        self.metrics_history.append(metrics_snapshot)

        # Keep only last 100 snapshots
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

        # Check for alerts
        await self.check_alerts(metrics_snapshot)

        logger.info("Monitoring cycle completed")

        return metrics_snapshot

    async def check_alerts(self, metrics: Dict):
        """Check metrics against alert thresholds"""
        alerts = []

        # Check API health
        for endpoint, data in metrics["health"].items():
            if not data.get("healthy"):
                alert_key = f"unhealthy_endpoint_{endpoint}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        "type": "api_health",
                        "severity": "high",
                        "message": f"Endpoint {endpoint} is unhealthy (status: {data.get('status')})"
                    })
                    self.alerts_sent.add(alert_key)

            if data.get("response_time", 0) > self.alert_thresholds["response_time"]:
                alert_key = f"slow_response_{endpoint}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        "type": "performance",
                        "severity": "medium",
                        "message": f"Endpoint {endpoint} response time is slow: {data['response_time']:.2f}s"
                    })
                    self.alerts_sent.add(alert_key)

        # Check security events
        security_events = metrics.get("security_events", {})
        if security_events.get("failed_logins", 0) > self.alert_thresholds["failed_logins"]:
            alert_key = "high_failed_logins"
            if alert_key not in self.alerts_sent:
                alerts.append({
                    "type": "security",
                    "severity": "high",
                    "message": f"High number of failed logins: {security_events['failed_logins']}"
                })
                self.alerts_sent.add(alert_key)

        if security_events.get("rate_limit_hits", 0) > self.alert_thresholds["rate_limit_hits"]:
            alert_key = "high_rate_limits"
            if alert_key not in self.alerts_sent:
                alerts.append({
                    "type": "security",
                    "severity": "medium",
                    "message": f"High number of rate limit hits: {security_events['rate_limit_hits']}"
                })
                self.alerts_sent.add(alert_key)

        # Check security headers
        if not metrics.get("security_headers", {}).get("all_secure", True):
            alert_key = "insecure_headers"
            if alert_key not in self.alerts_sent:
                alerts.append({
                    "type": "security",
                    "severity": "medium",
                    "message": "Security headers are not properly configured"
                })
                self.alerts_sent.add(alert_key)

        # Send alerts
        for alert in alerts:
            logger.warning(f"ALERT: {alert['message']}")
            self.send_alert_email(
                f"{alert['severity'].upper()} - {alert['type'].replace('_', ' ').title()}",
                alert['message']
            )

    async def generate_report(self) -> str:
        """Generate a monitoring report"""
        if not self.metrics_history:
            return "No metrics available yet"

        latest = self.metrics_history[-1]
        report = f"""
Authentication System Monitoring Report
Generated: {datetime.now().isoformat()}

📊 System Health:
"""

        # Health summary
        healthy_endpoints = sum(1 for ep in latest["health"].values() if ep.get("healthy"))
        total_endpoints = len(latest["health"])
        report += f"- API Endpoints: {healthy_endpoints}/{total_endpoints} healthy\n"

        # Security summary
        security_events = latest.get("security_events", {})
        report += f"- Failed Logins (recent): {security_events.get('failed_logins', 0)}\n"
        report += f"- Rate Limit Hits (recent): {security_events.get('rate_limit_hits', 0)}\n"

        # Security headers
        headers_secure = latest.get("security_headers", {}).get("all_secure", False)
        report += f"- Security Headers: {'✅ Configured' if headers_secure else '❌ Incomplete'}\n"

        # Performance metrics
        avg_response_time = sum(ep.get("response_time", 0) for ep in latest["health"].values()) / len(latest["health"])
        report += f"- Avg Response Time: {avg_response_time:.2f}s\n"

        report += "\n🚨 Active Alerts:\n"
        if self.alerts_sent:
            for alert in list(self.alerts_sent)[:5]:  # Show last 5 alerts
                report += f"- {alert}\n"
        else:
            report += "- No active alerts\n"

        return report

    async def continuous_monitoring(self, interval: int = 60):
        """Run continuous monitoring"""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        while True:
            try:
                await self.run_monitoring_cycle()

                # Generate periodic report
                if len(self.metrics_history) % 10 == 0:  # Every 10 cycles
                    report = await self.generate_report()
                    logger.info("Periodic Report:\n" + report)

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}")
                await asyncio.sleep(interval)

async def main():
    """Main monitoring function"""
    print("🔍 Starting Authentication System Monitor")
    print("=" * 50)

    async with AuthSystemMonitor() as monitor:
        # Run initial monitoring cycle
        print("Running initial monitoring cycle...")
        metrics = await monitor.run_monitoring_cycle()

        print("📊 Initial Metrics:")
        print(json.dumps(metrics, indent=2, default=str))

        # Generate report
        report = await monitor.generate_report()
        print("\n📋 Monitoring Report:")
        print(report)

        # Start continuous monitoring
        print("\n🔄 Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            await monitor.continuous_monitoring(interval=30)  # 30 second intervals
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    asyncio.run(main())
