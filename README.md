# Envoyou SEC Climate Compliance API

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
![Badge showing license type Business Source License 1.1 in blue color](https://img.shields.io/badge/License-BSL--1.1-blue.svg)
![Badge showing usage status Non-Commercial in orange color](https://img.shields.io/badge/Use-Non--Commercial-orange.svg)
![Badge showing re-license to Apache 2.0 scheduled for 2028 in green color](https://img.shields.io/badge/Re--License-Apache%202.0%20(2028)-green.svg)
![Badge showing project status MVP Global in brightblue color](https://img.shields.io/badge/Status-MVP%20Global-brightblue.svg)
![Badge showing build passing in success green color](https://img.shields.io/badge/Build-Passing-success.svg)

-----

[](https://www.python.org/downloads/release/python-3120/)
[](https://fastapi.tiangolo.com/)
[](https://python.langchain.com/docs/langgraph/)

The official backend for the [Envoyou](https://envoyou.com) platform. This service is designed as a **Trust-Critical Data Infrastructure** to automate compliance with the U.S. SEC's Climate Disclosure Rule.

## 📖 Overview

The Envoyou SEC Compliance API functions as an AI-driven, autonomous intelligence engine. The platform systematically gathers, validates, and structures Greenhouse Gas (GHG) emissions and climate risk data to enable U.S. public companies (particularly mid-caps) to meet their SEC reporting obligations with the highest degree of certainty and traceability.

Our core value proposition is **Forensic-Grade Traceability**, ensuring every data point is auditable and defensible before regulators.

## ✨ Key Features

- **SEC Compliance Automation**: Purpose-built to address the pain points of the SEC Climate Disclosure Rule, focusing on Scope 1 & 2 GHG emissions and material risk reporting.
- **Forensic-Grade Traceability**: Every calculation and data point is equipped with an immutable audit trail, linking data from primary sources to the final report.
- **Proprietary "Crosswalk" Engine**: Our core IP that intelligently links facility-level data (from the EPA) to corporate-level entities (SEC CIKs), solving a complex technical reporting challenge.
- **Multi-Agent AI Architecture**: Powered by a system of autonomous AI agents (built with LangGraph and Google Gemini) that collaborate on data acquisition, ETL, and auditing.
- **Intelligent Data Cross-Validation**: Automatically validates self-reported data against governmental and commercial data sources to identify inconsistencies before filing.
- **Audit-Ready Reports**: Generates structured outputs designed for direct integration into annual reports (10-Ks) and ready for third-party auditor verification.
- **Resilient Hybrid Data Strategy**: Utilizes licensed commercial data as the primary foundation and public data as a supplement to ensure data reliability regardless of government policy changes.

## 🤖 AI Agent Architecture

This platform doesn't just run scripts; it executes autonomous workflows using a collaborative multi-agent system:

1. **Acquisition Agent**: Dynamically ingests data from various governmental (EPA, NOAA) and commercial API sources.
1. **ETL & Crosswalk Agent**: Cleans, standardizes, and, most importantly, runs the "Crosswalk Engine" to link facility data to corporations.
1. **Audit Trail Agent**: Records every action, decision, and reasoning trace from other agents to ensure forensic-grade traceability.
1. **API Serving Agent**: Orchestrates the workflow and serves the final, processed, and audited data through secure API endpoints.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (Recommended)
- A Google Cloud account with an active Gemini API Key

### 1\. Environment Setup

Create a `.env` file from the example template. This file will be used to store your API keys and configuration.

```bash
cp .env.example .env
```

Fill in the required variables inside the `.env` file:

```env
# API Key for Google Gemini
GOOGLE_API_KEY="your_google_api_key_here"

# Other variables that might be needed (database, etc.)
DATABASE_URL="postgresql://user:password@host:port/dbname"
```

### 2\. Installation

Use the streamlined `requirements.txt` to install only the necessary dependencies for this AI project.

```bash
pip install -r requirements.txt
```

### 3\. Running the Server

For local development with live reloading:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. For interactive documentation, visit `http://localhost:8000/docs`.

### 3.1 Demo E2E (Emissions Calculation)

- Check latest emission factors:

```bash
curl 'http://localhost:8000/v1/environmental/factors/latest' \
  -H 'X-API-Key: demo_key'
```

- Calculate emissions (electricity & fuel) and get `transaction_id` in response:

```bash
curl -X POST 'http://localhost:8000/v1/environmental/emissions/calc' \
  -H 'Content-Type: application/json' -H 'X-API-Key: demo_key' \
  -d '{
    "scope":"scope2",
    "activities":[{"type":"electricity","amount":1000,"unit":"kWh"}]
  }'

curl -X POST 'http://localhost:8000/v1/environmental/emissions/calc' \
  -H 'Content-Type: application/json' -H 'X-API-Key: demo_key' \
  -d '{
    "scope":"scope1",
    "activities":[{"type":"fuel","amount":200,"unit":"liter","fuel":"diesel","notes":"genset","source_ref":"file:invoice-001.pdf"}]
  }'
```

- List audits (non-production only) with optional filters:

```bash
curl 'http://localhost:8000/v1/environmental/emissions/audits?limit=50&scope=scope1' \
  -H 'X-API-Key: demo_key'
```

- Lookup a single result by `transaction_id` (non-production only):

```bash
curl 'http://localhost:8000/v1/environmental/emissions/<transaction_id>' \
  -H 'X-API-Key: demo_key'
```

### 4\. Running the AI Agent Graph (For Testing)

You can test the AI workflow directly from the terminal:

```bash
python -m app.graph
```

This will execute the agent workflow and display the state evolution at each step.

## 🧪 Testing

This project uses `pytest`. To run the entire test suite:

```bash
pytest
```

-----

## Contributing

Pull requests are welcome. For major changes, please open an [issue](https://www.google.com/search?q=https://github.com/ENVOYou/envoyou-sec-api/issues) first to discuss what you would like to change.

-----

## License

This project is released under the **Business Source License 1.1 (BSL-1.1)**.

- For non-commercial use only.
- Will be automatically re-licensed to **Apache 2.0** in 2028.
- See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

## Contact

Maintained by [Husni Kusuma](https://github.com/hk-dev13)  
🌐 Website: [envoyou.com](https://envoyou.com)  
📧 More info: [info@envoyou.com](mailto:info@envoyou.com)

-----

> <p style="text-align: center;"\>© 2025 <a href="[https://envoyou.com](https://envoyou.com)"\>Envoyou</a> | All Rights Reserved</p>
> <p style="text-align: center;"\>Empowering Auditable Climate Compliance</p>
