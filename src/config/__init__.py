"""
Configuration Package
=====================
Loads and exposes the AI engine settings from engine_config.yaml.

Public API:
    get_settings()  → Settings  (singleton, cached after first call)
    load_settings() → Settings  (re-reads the YAML file every time)
    reset_settings()            (clears cache — use in unit tests only)

Usage:
    from src.config import get_settings

    cfg = get_settings()
    print(cfg.rule_engine.structuring_threshold)
"""
from src.config.settings import Settings, get_settings, load_settings, reset_settings

__all__ = ["Settings", "get_settings", "load_settings", "reset_settings"]
