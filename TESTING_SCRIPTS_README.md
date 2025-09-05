# Authentication System Testing Scripts

This directory contains comprehensive testing scripts for the authentication system, designed to validate security, performance, and reliability before and after deployment.

## 📋 Available Scripts

### 1. Load Testing (`load_test_auth.py`)
Tests authentication endpoints under load to validate rate limiting and performance.

**Features:**
- Concurrent user registration testing
- Login load testing with multiple users
- Rate limiting validation
- Response time analysis
- Statistical performance metrics

**Usage:**
```bash
cd /home/husni/project-permit-api
python scripts/load_test_auth.py
```

**Configuration:**
- `num_requests`: Number of requests to send (default: 100)
- `concurrent`: Number of concurrent requests (default: 10)
- `base_url`: API base URL (default: http://localhost:8000)

### 2. Stress Testing (`stress_test_db.py`)
Comprehensive stress testing for database connections and API endpoints.

**Features:**
- Database connection pooling tests
- Memory leak detection
- Concurrent API call testing
- Resource usage monitoring
- Sustained load testing

**Usage:**
```bash
cd /home/husni/project-permit-api
python scripts/stress_test_db.py
```

**Configuration:**
- `num_users`: Number of test users to create (default: 20)
- `num_requests`: Number of concurrent requests (default: 100)
- `duration`: Test duration in seconds (default: 60)

### 3. Monitoring & Alerting (`monitor_auth_system.py`)
Real-time monitoring and alerting system for the authentication infrastructure.

**Features:**
- API health monitoring
- Security event detection
- Performance metrics tracking
- Email alert notifications
- Security header validation
- Log analysis for suspicious activities

**Usage:**
```bash
cd /home/husni/project-permit-api
python scripts/monitor_auth_system.py
```

**Configuration:**
- `base_url`: API base URL (default: http://localhost:8000)
- `interval`: Monitoring interval in seconds (default: 60)
- Email settings via environment variables:
  - `SMTP_SERVER`
  - `SMTP_PORT`
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`
  - `ALERT_EMAIL`

### 4. CI/CD Testing (`ci_cd_auth_tests.py`)
Automated testing suite for CI/CD pipelines and deployment validation.

**Features:**
- Unit test execution
- Authentication-specific tests
- Security testing
- API integration tests
- Database migration validation
- Dependency checking
- Load performance testing
- Security scanning
- Comprehensive test reporting

**Usage:**
```bash
cd /home/husni/project-permit-api
python scripts/ci_cd_auth_tests.py
```

**Exit Codes:**
- `0`: All tests passed
- `1`: Some tests failed

## 🔧 Environment Setup

### Required Dependencies
```bash
pip install aiohttp requests python-dotenv
```

### Environment Variables for Monitoring
```bash
# SMTP Configuration for alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=admin@example.com

# Test Configuration
TEST_BASE_URL=http://localhost:8000
```

## 📊 Test Reports

### Load Test Results
- Total requests processed
- Successful vs failed requests
- Response time statistics (avg, median, 95th percentile)
- Requests per second
- Error analysis

### Stress Test Results
- Memory usage over time
- CPU utilization
- Database connection metrics
- API throughput
- Memory leak detection

### Monitoring Reports
- API health status
- Security events summary
- Performance metrics
- Active alerts
- Recommendations

### CI/CD Test Reports
- Test execution summary
- Pass/fail statistics
- Detailed test outputs
- Security recommendations
- Deployment readiness assessment

## 🚨 Alert Types

### High Priority
- API endpoints unhealthy
- High number of failed login attempts
- Security vulnerabilities detected
- Database connection failures

### Medium Priority
- Slow response times
- Rate limiting triggered
- Security headers misconfigured
- Memory usage spikes

## 📈 Performance Benchmarks

### Target Metrics
- API Response Time: < 2 seconds
- Error Rate: < 1%
- Concurrent Users: > 100
- Memory Usage: < 512MB
- CPU Usage: < 70%

### Monitoring Thresholds
- Response Time Alert: > 5 seconds
- Error Rate Alert: > 5%
- Failed Logins Alert: > 10/minute
- Rate Limit Alert: > 5/minute

## 🔒 Security Testing

### Automated Checks
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting effectiveness
- Security headers validation
- Authentication bypass attempts

### Manual Testing Recommendations
- Penetration testing
- Security audit review
- Code review for vulnerabilities
- Third-party dependency scanning

## 📝 Logging

All scripts generate detailed logs:
- Load tests: Console output with real-time metrics
- Stress tests: Memory and performance logs
- Monitoring: `/logs/auth_monitor.log`
- CI/CD: JSON test reports with timestamps

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
- name: Run Auth Tests
  run: |
    cd /home/husni/project-permit-api
    python scripts/ci_cd_auth_tests.py

- name: Load Testing
  run: |
    python scripts/load_test_auth.py

- name: Security Scan
  run: |
    python scripts/stress_test_db.py
```

## 🐛 Troubleshooting

### Common Issues
1. **Connection Refused**: Ensure API server is running
2. **Import Errors**: Install required dependencies
3. **SMTP Errors**: Check email configuration
4. **Permission Errors**: Ensure proper file permissions

### Debug Mode
Set environment variable for verbose logging:
```bash
export DEBUG=true
```

## 📞 Support

For issues with testing scripts:
1. Check the logs for detailed error messages
2. Verify API server is running and accessible
3. Ensure all dependencies are installed
4. Review environment configuration
5. Check file permissions and paths

## 🔄 Updates

Keep testing scripts updated with:
- New authentication features
- Security patches
- Performance improvements
- API endpoint changes
- Monitoring requirements
