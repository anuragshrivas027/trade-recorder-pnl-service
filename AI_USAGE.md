# Trade Recorder & PnL Service — AI Usage Disclosure

## 1. Overview

AI tools were used as development assistants while building the Trade Recorder & PnL Service. They helped with understanding the requirements, planning the implementation, improving code, troubleshooting issues, and preparing project documentation.

AI assistance was used as a support tool, not as a replacement for running and testing the application.

## 2. Areas Where AI Assisted

### Requirement Analysis and Design

AI assistance helped break down the requirements into API endpoints, database models, trade-processing logic, position calculations, and reconciliation functionality.

### Implementation Support

AI assistance helped with the structure of the FastAPI application, SQLAlchemy database integration, Pydantic validation, and service-layer implementation.

### Debugging

AI assistance helped investigate implementation issues and identify possible fixes related to database operations, duplicate trades, timestamp handling, and test behavior.

### Testing

AI assistance helped prepare automated tests covering API behavior, validation, duplicate handling, position calculations, overselling, and reconciliation.

### Documentation

AI assistance helped draft the README, system design documentation, setup instructions, and this AI usage disclosure.

## 3. Verification

The application was run locally, and the automated test suite completed successfully with seven passing tests.

The API was also manually checked for trade submission, price updates, position calculations, and rejection of an oversell request.

The automated tests use SQLite for isolated testing. The PostgreSQL connection and selected API scenarios were checked manually. Dedicated PostgreSQL concurrency tests have not yet been completed.

These checks do not constitute full production verification. Additional PostgreSQL integration, concurrency, security, and deployment testing would be needed before production use.

## 4. Developer Responsibility

The developer is responsible for understanding the implementation, reviewing the generated code, checking its correctness, and explaining the design decisions.

AI-generated suggestions may contain mistakes and must be reviewed and tested before being accepted.

## 5. Limitations

AI assistance does not guarantee that the application is free from bugs or security issues. The current implementation is intended as a take-home project and would need further testing and hardening before production deployment.