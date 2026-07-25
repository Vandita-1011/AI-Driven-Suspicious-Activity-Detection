"""
AI-Driven Suspicious Activity Detection System
===============================================
AI Engine Root Package  (src/)

This package is the complete, self-contained AI engine for autonomous
Anti-Money Laundering (AML) investigation.  It operates independently
of any web framework and is designed to be consumed by a FastAPI
backend built separately by another developer.

Architecture (pipeline order):
    User  →  Orchestrator
          →  Data Loader
          →  Smart Preprocessing
          →  Behaviour Profiling
          →  EDA  (on-demand)
          →  Feature Engineering
          →  Rule Engine
          →  Behaviour Engine
          →  Statistical Engine
          →  ML Anomaly Engine
          →  AML Pattern Engine
          →  Smart Risk Fusion
          →  Explainability
          →  Recommendation
          →  Alert Prioritization
          →  API Interface  →  FastAPI  (separate developer)

Sub-packages:
    config          Configuration management (YAML-based)
    constants       Project-wide enumerations and string constants
    exceptions      Custom exception hierarchy
    utils           Shared utilities (logger, timer, validators, IO)
    interfaces      Abstract base classes — contracts between modules
    data            Data loading, schema definitions, DatasetContext
    preprocessing   Data cleaning and multi-table enrichment
    profiling       Per-customer / per-account behaviour profiling
    eda             Exploratory data analysis (triggered on demand)
    features        Feature engineering pipeline (3 extractors + pipeline)
    engines         Five detection engines + Smart Risk Fusion
    explainability  Evidence-based explanation generation (no SHAP/LIME)
    recommendation  Investigator action recommendations
    alerts          Alert prioritization and deduplication
    orchestrator    Master pipeline coordinator
    api_interface   Typed request / response models for the API layer
"""

__version__ = "0.1.0"
__author__ = "AML AI Engine Team"
__project__ = "AI-Driven Suspicious Activity Detection — HexBreach Hackathon"
