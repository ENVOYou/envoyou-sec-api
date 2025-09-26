# Migration from CEVS to SEC API

## Overview

This document outlines the migration from the original CEVS (Composite Environmental Verification Score) project to the focused Envoyou SEC Compliance API.

## Background

**Original CEVS Project:**

- Multi-source environmental data aggregation
- Composite scoring from EPA, EEA, EDGAR, ISO, Amdalnet
- Broad environmental performance metrics
- Target market: General environmental compliance

**New SEC API Focus:**

- SEC Climate Disclosure compliance (Scope 1 & 2)
- Auditable emissions calculation
- EPA validation for anomaly detection
- SEC-ready export formats (10-K friendly)

## Disabled Legacy Endpoints

The following endpoints have been disabled to maintain focus:

### Authentication & User Management

- `/auth/*` - User authentication system
- `/user/*` - User profile management
- `/admin/*` - Legacy admin endpoints

### CEVS-Specific Features

- `/global/*` - Multi-source data aggregation
- `/permits/*` - Environmental permits data
- `/cloudflare/*` - Infrastructure management

### Legacy Data Sources

- EEA industrial pollution trends
- EDGAR global emissions data
- ISO certification aggregation
- Amdalnet permit integration

## Active SEC API Endpoints

### Core Functionality

- `POST /v1/emissions/calculate` - Scope 1 & 2 emissions calculation
- `GET /v1/emissions/factors` - Emission factors management
- `GET /v1/emissions/units` - Supported units

### Validation & Compliance

- `POST /v1/validation/epa` - EPA cross-validation
- `POST /v1/admin/mappings` - Company-facility mapping

### Export & Reporting

- `GET /v1/export/sec/cevs/{company}` - CEVS data export
- `POST /v1/export/sec/package` - SEC filing package generation

### Audit & Governance

- `POST /v1/audit` - Audit trail creation
- `GET /v1/audit` - Audit trail retrieval

## Migration Benefits

1. **Focused Scope**: Clear SEC compliance focus vs. broad environmental metrics
2. **Simplified Architecture**: Reduced complexity and dependencies
3. **Better Performance**: Fewer data sources and processing overhead
4. **Clearer Value Proposition**: Specific SEC Climate Disclosure compliance
5. **Easier Maintenance**: Focused codebase with clear boundaries

## Re-enabling Legacy Features

If legacy CEVS features are needed in the future:

1. Uncomment disabled routers in `app/api_server.py`
2. Restore authentication middleware dependencies
3. Update API documentation and tests
4. Consider creating separate microservices for different concerns

## API Documentation

- **Current Focus**: SEC Climate Disclosure (Scope 1 & 2)
- **Target Users**: Public companies requiring SEC climate reporting
- **Key Features**: Auditable calculations, EPA validation, SEC-ready exports
- **Authentication**: API key based (simplified from JWT + RBAC)

This migration ensures the API serves its intended purpose effectively while maintaining the option to expand functionality in the future.
