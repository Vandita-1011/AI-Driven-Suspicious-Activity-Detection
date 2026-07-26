# AI-Driven Suspicious Activity Detection

## Overview

AI-Driven Suspicious Activity Detection is an intelligent Anti-Money Laundering (AML) analytics platform designed to assist financial institutions in identifying potentially suspicious financial activities using explainable artificial intelligence.

The platform combines traditional rule-based detection with statistical analysis, machine learning, behavioral profiling, AML pattern recognition, and explainable AI to prioritize suspicious transactions for investigation. It provides investigators with a unified dashboard, automated risk assessment, alert prioritization, investigation workflows, and AI-generated explanations to improve operational efficiency while reducing false positives.

---

## Problem Statement

Financial institutions process millions of financial transactions every day. Traditional AML systems rely heavily on static rules, often generating large numbers of false positives that require extensive manual review.

This project aims to improve suspicious activity detection by combining multiple AI-driven detection techniques with explainable intelligence to identify high-risk transactions more accurately and assist investigators in making faster, more informed decisions.

---

## Solution Approach

The platform follows a multi-stage intelligent analysis pipeline.

### 1. Data Ingestion

Transaction datasets are uploaded through the web interface.

Supported inputs include:

- CSV transaction files
- Structured transaction records

### 2. Data Validation & Preprocessing

The uploaded data is:

- Validated
- Cleaned
- Normalized
- Enriched
- Prepared for downstream AI analysis

### 3. Feature Engineering

The platform generates multiple analytical features including:

- Transaction frequency
- Average transaction amount
- Cash movement ratios
- Temporal behaviour
- Customer activity trends
- Network relationship indicators

### 4. Behaviour Profiling

Historical customer activity is analysed to establish behavioural baselines.

The system identifies deviations such as:

- Unusual transaction frequency
- Abnormal transfer amounts
- Sudden spikes in activity
- Unexpected account interactions

### 5. Multi-Engine Risk Analysis

The AI intelligence layer combines multiple detection techniques:

- Rule-Based Detection
- Statistical Detection
- Machine Learning Detection
- AML Pattern Detection
- Behaviour Analysis

Each engine independently evaluates transaction risk before contributing to the final assessment.

### 6. Risk Fusion

Outputs from all detection engines are combined to generate a unified risk score.

Transactions are classified into:

- Low Risk
- Medium Risk
- High Risk
- Critical Risk

### 7. Explainable AI

Instead of only assigning a risk score, the platform explains why a transaction was flagged by highlighting the contributing behavioural patterns and detection results.

This improves transparency and assists investigators during manual review.

### 8. Recommendation Engine

Based on the final risk assessment, the platform recommends actions such as:

- Continue Monitoring
- Manual Review
- Enhanced Due Diligence
- Escalate Investigation

### 9. Investigation Dashboard

Investigators can:

- Review alerts
- Inspect transaction details
- View AI-generated explanations
- Track investigations
- Generate reports

---

## Key Features

- AI-powered suspicious activity detection
- Explainable AI
- Behaviour profiling
- Rule-based detection
- Statistical anomaly detection
- Machine learning analysis
- AML pattern recognition
- Risk prioritization
- Alert management
- Investigation dashboard
- Report generation
- REST API integration
- Modular AI architecture

---

## Project Architecture

```
                                    User
                                     │
                          React Frontend Dashboard
                                     │
                           FastAPI Backend APIs
                                     │
                          AI Intelligence Layer
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │                                                          │
   Data Loader                                            Data Validation
        │                                                          │
   Preprocessing                                        Feature Engineering
        │                                                          │
 Behaviour Profiling                                    Multi-Engine Analysis
        │                                                          │
        │              ┌───────────────┬───────────────┬──────────┘
        │              │               │               │
        │         Rule Engine    Statistical      ML Engine     Pattern Engine
        │              │           Engine             │               │
        │              └───────────────┴───────┬───────┴───────────────┘
        │                                       │
        │                              Risk Fusion Engine
        │                                       │
        │                            Explainability Engine
        │                                       │
        │                            Recommendation Engine
        │                                       │
        └───────────────────────────► Alerts & Investigation
```

---

## Technology Stack

### Backend

- Python
- FastAPI

### Frontend

- React
- Vite

### AI / Machine Learning

- Scikit-learn
- Pandas
- NumPy

### Configuration

- YAML

### Testing

- Pytest

---

## Dataset Information

The project uses publicly available transaction datasets together with carefully generated synthetic transaction data.

### Public Dataset

**IBM AML Transaction Dataset**

Source:

https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml

The IBM AML dataset was used to understand realistic transaction structures and Anti-Money Laundering scenarios during development and testing.

### Synthetic Dataset

Since publicly available datasets cannot represent every suspicious behaviour required for experimentation, synthetic transaction records were generated.

The synthetic dataset was created solely for research, testing, and demonstration purposes.

No real customer information is included.

#### Synthetic Data Schema

The synthetic records follow a banking transaction structure including fields such as:

- Customer ID
- Account ID
- Transaction ID
- Transaction Timestamp
- Transaction Amount
- Transaction Type
- Merchant Category
- Source Account
- Destination Account
- Geographic Information
- Risk Labels

#### Synthetic Data Generation Logic

Synthetic transactions were generated using realistic banking assumptions.

The generated scenarios include:

- Large-value transfers
- Rapid movement of funds
- Structuring (multiple small transactions)
- Repeated transfers between linked accounts
- Abnormal customer behaviour
- High-frequency transactions
- High-risk transaction patterns

The generated records follow the IBM dataset schema wherever applicable to maintain consistency during testing.

---

## Assumptions

- Customer identifiers are anonymized.
- Synthetic records represent realistic banking behaviour.
- Risk scores are decision-support indicators.
- Final investigation decisions remain the responsibility of human investigators.

---

## AI Assistance Disclosure

The following AI-assisted development tools were used during implementation:

- Claude AI
- ChatGPT

These tools were used for software development assistance, debugging, documentation, and code generation.

Final implementation, integration, testing, and validation were performed by the project team.

---

## Prerequisites

Before running the project, ensure the following software is installed:

- Python 3.11 or later
- Node.js (LTS) with npm
- Git

Verify the installation:

```bash
python --version
node --version
npm --version
git --version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<vandita-1011>/AI-Driven-Suspicious-Activity-Detection.git
cd AI-Driven-Suspicious-Activity-Detection
```

### Backend Setup

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Install the additional dependency required for file uploads:

```bash
pip install python-multipart
```

### Frontend Setup

```bash
cd frontend
npm install
cd ..
```

---

## Running the Project

The application consists of two independent services:

- FastAPI Backend
- React Frontend

Both services must be running simultaneously.

### Step 1 — Start the Backend

From the project root:

```bash
uvicorn backend.app:app --reload
```

Backend URL:

```
http://127.0.0.1:8000
```

Swagger Documentation:

```
http://127.0.0.1:8000/docs
```

### Step 2 — Start the Frontend

Open another terminal.

```bash
cd frontend
npm run dev
```

Frontend URL:

```
http://localhost:5173
```

### Step 3 — Using the Application

1. Start both backend and frontend.
2. Open the frontend application.
3. Upload a transaction dataset (CSV).
4. The platform preprocesses the uploaded data.
5. AI engines analyse transactions.
6. Risk scores and explanations are generated.
7. View:
   - Dashboard
   - Alerts
   - Investigation Details
   - AI Explanations
   - Reports

---

## API Documentation

Interactive API documentation is automatically available once the backend is running.

Swagger UI:

```
http://127.0.0.1:8000/docs
```

OpenAPI Specification:

```
http://127.0.0.1:8000/openapi.json
```

---

## Running Tests

Run all tests:

```bash
pytest
```

Run a specific test:

```bash
pytest tests/test_ai_service.py
```

Run the backend server:

```bash
uvicorn backend.app:app --reload
```

---

## Project Structure

```
AI-Driven-Suspicious-Activity-Detection/
│
├── backend/
│   ├── database/
│   ├── exceptions/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── app.py
│   └── requirements.txt
│
├── frontend/
│
├── src/
│
├── tests/
│
├── logs/
│
├── outputs/
│
├── README.md
│
└── .gitignore
```

---

## Data Sources

**IBM AML Transaction Dataset**

https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml

**Synthetic Dataset**

Generated by the project team using realistic banking transaction assumptions for testing and demonstration purposes.

---

## Future Improvements

- Real-time transaction streaming
- Graph Neural Network based relationship analysis
- Continuous investigator feedback learning
- Adaptive risk scoring
- Fraud network visualization
- Streaming anomaly detection
- Automated model retraining
- LLM-assisted Suspicious Activity Report (SAR) generation
- Apache Kafka based real-time event processing

---

## Repository Notes

- This repository was created and maintained throughout the hackathon.
- The commit history reflects the complete development process.
- The solution is implemented as a generic banking-domain suspicious activity detection platform.
- No organization-specific names, branding, or proprietary references have been used in the repository.

---

## License

This repository is intended for educational and hackathon purposes.

---

## Acknowledgements

- IBM AML Transaction Dataset
- Kaggle
- FastAPI
- React
- Vite
- Scikit-learn
- NumPy
- Pandas
- Python Community
