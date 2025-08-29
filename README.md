# Envoyou CEVS Aggregator API

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
<!-- [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) -->
![Badge showing license type Business Source License 1.1 in blue color](https://img.shields.io/badge/License-BSL--1.1-blue.svg) 
![Badge showing usage status Non-Commercial in orange color](https://img.shields.io/badge/Use-Non--Commercial-orange.svg)
![Badge showing re-license to Apache 2.0 scheduled for 2028 in green color](https://img.shields.io/badge/Re--License-Apache%202.0%20(2028)-green.svg)
![Badge showing project status MVP Global in brightblue color](https://img.shields.io/badge/Status-MVP%20Global-brightblue.svg)
![Badge showing build passing in success green color](https://img.shields.io/badge/Build-Passing-success.svg)

The official backend API for the [Envoyou](https://envoyou.com) platform. This service aggregates environmental data from multiple global sources to calculate a **Composite Environmental Verification Score (CEVS)**, providing a standardized metric for corporate environmental performance.

## 📖 Overview

The CEVS Aggregator API acts as a robust data pipeline and scoring engine. It connects to various official data sources (e.g., EPA, EEA, ISO), normalizes the incoming data into a consistent schema, and applies a sophisticated scoring algorithm to generate the CEVS for a given company.

## ✨ Key Features

- **Multi-Source Data Aggregation**: Integrates with key environmental data providers:
  - **EPA (USA)**: Facility and power plant emissions data (Envirofacts, CAMPD).
  - **EEA (Europe)**: Industrial pollution and renewable energy statistics.
  - **EDGAR**: Global urban emissions data.
  - **ISO**: ISO 14001 certification status.
- **Composite Environmental Verification Score (CEVS)**: A proprietary scoring model that provides a holistic view of a company's environmental impact and commitment.
- **Secure API Access**: All critical endpoints are protected by API key authentication.
- **Tier-Based Rate Limiting**: Different usage tiers (Basic, Premium) to manage API load.
- **Robust Caching**: In-memory and file-based caching for improved performance and reduced external API calls.
- **Standardized Data Schemas**: All data is normalized into a clean, predictable format.
- **Asynchronous Framework**: Built with FastAPI for high performance and scalability.
- **Dockerized**: Ready for containerized deployment in any environment.

## 📚 API Documentation

For detailed information on all available endpoints, request/response formats, and usage examples, please refer to the official **[API Documentation](API_DOCUMENTATION.md)**.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (Recommended)

### 1. Environment Setup

First, create a `.env` file from the example template:

```bash
cp .env.example .env
```

Now, open the `.env` file and configure the necessary variables. At a minimum, you should set your API keys. For development, you can use the demo keys.

```env
# .env
# --- General Server Configuration ---
PORT=8000
LOG_LEVEL=DEBUG

# --- Security ---
# For production, generate secure keys. See generate_keys.py
API_KEYS="demo_key_basic_2025:DemoApp:basic,demo_key_premium_2025:PremiumApp:premium"
MASTER_API_KEY="your_secure_master_key_for_admin_tasks"

# --- External API Keys ---
CAMPD_API_KEY="YOUR_EPA_CAMPD_API_KEY" # Get from https://www.epa.gov/airmarkets/cam-api-portal
```

### 2. Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Running the Server

#### Local Development (with Uvicorn)

The server supports live reloading, which is ideal for development.

```bash
uvicorn app.api_server:app --reload --port 8000 --log-level debug
```

The API will be available at `http://localhost:8000`.

#### Production (with Docker)

Using Docker is the recommended way to run the application in production.

```bash
# Build and run the services in the background
docker-compose up --build -d

# Check the logs
docker-compose logs -f

# Stop the services
docker-compose down
```

## ⚙️ Configuration

The application is configured via environment variables, which are loaded by `pydantic-settings` from the `.env` file. Key configuration options are defined in `app/config.py`.

- `PORT`: The port the server will run on.
- `LOG_LEVEL`: The logging level (e.g., `DEBUG`, `INFO`, `WARNING`).
- `API_KEYS`: A comma-separated list of valid API keys and their tiers.
- `CAMPD_API_KEY`: Your API key for the EPA CAMPD service.
- `*_XLSX_PATH`: Paths to local reference data files (EDGAR, ISO, Policy).

## 🧪 Running Tests

The project uses `pytest` for testing.

```bash
pytest
```
---
## Contributing
Pull requests are welcome. For major changes, please open an [issue](https://github.com/hk-dev13/project-permit-api/issues) first to discuss what you would like to change.

---
## License
This project is released under the **Business Source License 1.1 (BSL-1.1)**.  
- Non-commercial use only.  
- Will be automatically re-licensed to **Apache 2.0** in 2028.  
- See the [LICENSE](LICENSE) file for details.

<!-- ### Badges
![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-blue.svg)
![Use: Non-Commercial](https://img.shields.io/badge/Use-Non--Commercial-orange.svg)
![Re-License: Apache 2.0 (2028)](https://img.shields.io/badge/Re--License-Apache%202.0%20(2028)-green.svg)
![Status: MVP Global](https://img.shields.io/badge/Status-MVP%20Global-brightblue.svg)
![Build: Passing](https://img.shields.io/badge/Build-Passing-success.svg) -->

## Acknowledgements
- [FastAPI](https://fastapi.tiangolo.com/)  
- [Uvicorn](https://www.uvicorn.org/)  
- [Pydantic](https://docs.pydantic.dev/)  

## Contact
Maintained by [Husni Kusuma](https://github.com/hk-dev13)  
🌐 Website: [envoyou.com](https://envoyou.com)  
📧 More info: [info@envoyou.com](mailto:info@envoyou.com)  

---
Made with ❤️ by [Envoyou](https://envoyou.com) — Empowering Global Environmental Transparency 🌍
