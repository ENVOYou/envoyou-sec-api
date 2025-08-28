# ENVOYOU.COM: The Environmental Verification Platform

![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-blue.svg)
![Use: Non-Commercial](https://img.shields.io/badge/Use-Non--Commercial-orange.svg)
![Re-License: Apache 2.0 (2028)](https://img.shields.io/badge/Re--License-Apache%202.0%20(2028)-green.svg)
![Status: MVP Global](https://img.shields.io/badge/Status-MVP%20Global-brightblue.svg)
![Build: Passing](https://img.shields.io/badge/Build-Passing-success.svg)

---

### 🚀 Turning fragmented environmental data into a single, verifiable score that reflects an entity's true environmental commitment.

**ENVOYOU.COM** is a multidimensional framework that integrates diverse environmental datasets to generate a **Comprehensive Environmental Verification Score (CEVS)**. This platform provides a unified, developer-friendly API for businesses, analysts, and ESG investors to access structured and actionable environmental insights.

## Key Features

- **Multi-Source Integration**: Aggregates data from global and national sources like the EPA, KLHK, ISO, EEA, and more.
- **Comprehensive Scoring (CEVS)**: Utilizes a sophisticated, multi-criteria methodology to calculate a single, holistic environmental performance score.
- **Standardized REST API**: Offers a clean, predictable, and well-documented API for easy integration.
- **Developer-Friendly**: Provides automatic OpenAPI (Swagger) documentation for all endpoints.
- **Modular Architecture**: Built with a clean, extensible structure that makes it easy to add new data sources and scoring components.

---

## The CEVS Framework

The CEVS is calculated based on five core components:

1.  **Regulatory Compliance**: Foundational data from bodies like the US EPA and Indonesia's KLHK, covering emissions, waste management, and regulatory violations.
2.  **Environmental Management System (EMS) Maturity**: Assesses the robustness of a company's EMS, primarily using ISO 14001 certification data.
3.  **Environmental Performance Indicators (EPI)**: Quantitative metrics beyond basic compliance, such as energy/water consumption, waste volumes, and GHG emissions (Scope 1, 2, & 3).
4.  **Supply Chain Sustainability**: Insights into supplier performance using data from platforms like EcoVadis and Sedex.
5.  **Eco-Friendly Product/Material Certifications**: Data from product-level certifications like LEI, COSMOS, and Cradle to Cradle.

---

## Development Roadmap

This project will be developed in four distinct phases:

- **Phase 1: US-Focused Proof-of-Concept**: Build the initial CEVS prototype focusing on entities in the United States, leveraging the EPA Envirofacts API and ISO 14001 data to validate the core methodology.

- **Phase 2: Global Data Partnerships**: Expand data sources by forming strategic partnerships with international bodies (UNEP, EEA), national agencies (KLHK, BPS in Indonesia), and sustainability platforms (EcoVadis, GBCI).

- **Phase 3: Robust Data Harmonization Protocol**: Develop a sophisticated data harmonization protocol with standardized taxonomies and algorithms to normalize data from diverse sources into a consistent and comparable format.

- **Phase 4: Pilot with Multinational Entities**: Test the mature CEVS framework in real-world scenarios with a diverse group of multinational corporations and financial institutions to gather feedback and refine the scoring model.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Poetry (for dependency management, optional)
- An API key for the CAMPD service (see Configuration).

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hk-dev13/project-permit-api.git
    cd project-permit-api
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure your environment:**
    Create a `.env` file by copying the `.env.example` file. Add any necessary API keys (e.g., `CAMPD_API_KEY`).

4.  **Run the development server:**
    ```bash
    uvicorn app.api_server:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

---

## API Usage

### Authentication

An API key is required for all `/global/*` endpoints. The local permit endpoints are currently public.

Provide your API key in one of the following ways:
- **Authorization Header (Recommended)**: `Authorization: Bearer <your_api_key>`
- **X-API-Key Header**: `X-API-Key: <your_api_key>`

### Interactive Documentation

Once the server is running, interactive OpenAPI (Swagger) documentation is available at:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
