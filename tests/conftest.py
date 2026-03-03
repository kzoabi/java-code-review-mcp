"""pytest configuration and shared fixtures."""
import os
import sys
import textwrap
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture()
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture()
def fixture_path():
    """Return a callable that builds a path to a fixture file."""
    def _path(filename):
        return os.path.join(FIXTURES_DIR, filename)
    return _path


@pytest.fixture()
def default_config():
    """Return the default tool configuration."""
    from src.config.loader import DEFAULT_CONFIG
    return DEFAULT_CONFIG.copy()


@pytest.fixture()
def jbct_config(default_config):
    """Config with JBCT enabled."""
    cfg = default_config.copy()
    cfg['jbct_profile'] = 'full'
    return cfg


@pytest.fixture()
def spring_config(default_config):
    """Config with Spring analysis enabled."""
    cfg = default_config.copy()
    cfg['spring_enabled'] = True
    return cfg
