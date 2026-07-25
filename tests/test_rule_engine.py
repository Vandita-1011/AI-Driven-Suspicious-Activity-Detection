import pytest
import pandas as pd

from src.engines.rule_engine import RuleEngine
from src.interfaces.base_engine import EngineResult


def test_rule_engine_empty_df():
    engine = RuleEngine()
    df = pd.DataFrame()
    result = engine.run(df)
    assert isinstance(result, EngineResult)
    assert result.scores.empty
