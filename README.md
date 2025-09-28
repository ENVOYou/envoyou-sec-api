# Envoyou SEC API

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-success.svg)](https://github.com/ENVOYou/envoyou-sec-api/actions)
[![Security](https://img.shields.io/badge/security-GitGuardian-orange.svg)](https://github.com/ENVOYou/envoyou-sec-api/actions)

A comprehensive backend service for SEC Climate Disclosure compliance, providing auditable greenhouse gas (GHG) calculation, validation, and report export features tailored for public companies.

## 📚 Documentation

- [Goals & Key Features (Internal)](docs/GOALS.md)
- [Metrics of Success (MVP)](docs/METRICS.md)
- [SEC Export — Sample Outputs](docs/SEC_EXPORT_SAMPLES.md)
- [Security Plan](docs/SECURITY_PLAN.md)
- [Partnering Strategy](docs/PARTNERING.md)
- [Admin Mapping Guide](docs/ADMIN_MAPPING.md)
- [Security Prevention Guide](SECURITY_PREVENTION_GUIDE.md)

## 🚀 Features

- **Forensic-Grade Traceability**: Every calculation stores inputs, emission factors, and sources in an immutable audit trail
- **EPA Cross-Validation**: Automatic comparison against public EPA datasets to flag discrepancies
- **SEC-Ready Exports**: Generate complete filing packages (JSON/CSV) for 10-K attachments
- **RBAC Security**: Role-based access control with JWT authentication
- **Automated Testing**: Comprehensive test suite with CI/CD integration
- **Security Scanning**: GitGuardian + TruffleHog integration for credential protection

## 📊 API Endpoints

### Core Endpoints
- `POST /v1/emissions/calculate` — Calculate Scope 1 & 2 emissions with audit trail
- `POST /v1/validation/epa` — Cross-validate against EPA data with quantitative deviation
- `POST /v1/export/sec/package` — Generate complete SEC filing package (zip)

### Export Endpoints
- `GET /v1/export/sec/cevs` — Export CEVS data (JSON/CSV)
- `GET /v1/export/sec/audit` — Export audit trail (CSV)

### Admin Endpoints (Premium)
- `POST /v1/admin/mappings` — Create/update company-facility mapping
- `GET /v1/admin/mappings/{company}` — Get mapping details
- `GET /v1/admin/mappings` — List all mappings
- `POST /v1/audit` — Create audit entry
- `GET /v1/audit` — List audit entries with filters

## 🎯 Key Goals

- **Single-Purpose MVP**: Calculate Scope 1 and Scope 2 emissions, produce auditable calculation records, and export SEC-ready reporting tables
- **Forensic-Grade Traceability**: Every calculation stores inputs, emission factors, and sources in an immutable AuditTrail
- **Cross-Validation**: Automatic comparison against public EPA datasets to flag significant discrepancies
- **Security First**: Comprehensive credential protection and automated security scanning

## 🛠️ Core Components

- **Emissions Calculator**: Advanced Scope 1 & 2 calculation engine with multiple fuel types and grid regions
- **AuditTrail System**: Immutable repository storing inputs, factors, source URLs, and timestamps
- **Validation Service**: EPA data comparison with configurable deviation thresholds
- **SEC Exporter**: 10-K friendly tables and notes generator
- **RBAC Middleware**: Role-based access control for admin and audit endpoints
- **Security Layer**: Pre-commit hooks, GitGuardian scanning, and credential protection

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL or SQLite
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ENVOYou/envoyou-sec-api.git
   cd envoyou-sec-api
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   # For local development
   export DATABASE_URL="sqlite:///./app.db"
   alembic upgrade head
   ```

5. **Start development server**
   ```bash
   uvicorn app.api_server:app --reload --port 8000
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 💻 Quick Example

### Calculate Emissions and Generate SEC Package

```bash
# 1. Calculate emissions with audit trail
curl -X POST "http://localhost:8000/v1/emissions/calculate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
    "scope2": {"kwh": 500000, "grid_region": "RFC"}
  }'

# 2. Cross-validate against EPA data
curl -X POST "http://localhost:8000/v1/validation/epa" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
    "scope2": {"kwh": 500000, "grid_region": "RFC"}
  }'

# 3. Generate complete SEC filing package
curl -X POST "http://localhost:8000/v1/export/sec/package" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
    "scope2": {"kwh": 500000, "grid_region": "RFC"}
  }'
```

### Response Example

```json
{
  "status": "success",
  "company": "Demo Corp",
  "emissions": {
    "scope1_co2e": 53.02,
    "scope2_co2e": 250.5,
    "total_co2e": 303.52
  },
  "audit_trail_id": "audit_123456789",
  "package_url": "/exports/demo_corp_sec_package.zip"
}
```

See [E2E Demo](docs/E2E_DEMO.md) for complete workflow examples.

## 🧪 Testing

### Run Tests

```bash
# Set test database to avoid touching production
export TEST_DATABASE_URL="sqlite:///./test.db"

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_emissions_calculate.py -v
```

### Test Categories

- **Unit Tests**: Core calculation logic
- **Integration Tests**: API endpoints and database
- **Security Tests**: Credential protection and RBAC
- **E2E Tests**: Complete workflow validation

## 🚀 Production Deployment

### Environment Variables

```bash
# Required for production
DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
API_KEY=your_secure_api_key
JWT_SECRET_KEY=your_jwt_secret
```

### Security Checklist

- ✅ Never commit production secrets
- ✅ Use environment variables for all credentials
- ✅ Enable GitGuardian scanning
- ✅ Run security checks before deployment
- ✅ Backup database before migrations

### Deployment Platforms

- **Railway**: Automatic deployment from GitHub
- **Vercel**: Serverless deployment
- **Docker**: Container-based deployment
- **AWS/GCP**: Cloud platform deployment

## 📈 Project Status

- ✅ **MVP Complete**: Core emissions calculation and SEC export
- ✅ **Security Hardened**: Comprehensive credential protection
- ✅ **Production Ready**: Deployed and tested
- 🔄 **Active Development**: Continuous improvements and features

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run security checks (`./scripts/security-check.sh`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

**Maintainer**: Husni Kusuma — [@hk-dev13](https://github.com/hk-dev13)

- 🌐 Website: [envoyou.com](https://envoyou.com)
- 📧 Email: [info@envoyou.com](mailto:info@envoyou.com)
- 📚 Documentation: [docs.envoyou.com](https://docs.envoyou.com)

---

<p align="center">
  <strong>Empowering SEC Climate Disclosure Compliance</strong><br>
  Built with ❤️ by the Envoyou Team
</p>
