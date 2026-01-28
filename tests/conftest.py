# tests/conftest.py
"""
Pytest configuration that:
1) Makes src/ importable (so `from footballmvp...` works).
2) Runs tests with CWD set to tests/ (so relative writes land here).
3) Ensures a tests/artifacts/ folder exists.
4) Provides a fast local SparkSession per test (function-scoped).
"""

import os
import sys
from pathlib import Path
import pytest


# 1) Ensure `src/` is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# 2) Auto-chdir to `tests/` for the whole session
@pytest.fixture(scope="session", autouse=True)
def _chdir_to_tests():
    tests_dir = Path(__file__).parent.resolve()
    orig = Path.cwd()
    os.chdir(tests_dir)
    try:
        yield
    finally:
        os.chdir(orig)


# 3) Ensure artifacts/ exists for images/extra outputs
@pytest.fixture(scope="session", autouse=True)
def _ensure_artifacts_dir():
    Path("artifacts").mkdir(exist_ok=True)


# 4) Local Spark fixture (fresh per test)
@pytest.fixture(scope="function")
def spark():
    """Small local Spark with good defaults for CPU runs."""
    from pyspark.sql import SparkSession

    cores = os.cpu_count() or 8
    shuffle_parts = max(cores * 2, 16)

    spark = (
        SparkSession.builder
        .master(f"local[{cores}]")
        .appName("FootballMVP-UnitTests")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.shuffle.partitions", str(shuffle_parts))
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .getOrCreate()
    )
    yield spark
    spark.stop()
