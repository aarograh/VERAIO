"""Shared pytest fixtures for the verain unit test suite."""

import pytest

from verain.plugins import PluginRegistry
from verain.templates import reset_directory_processor_cache


@pytest.fixture(autouse=True)
def _reset_plugin_registry_cache():
    """Drop the ``PluginRegistry`` cache around every test.

    Cheap (it only re-scans entry points and manifest files, not the
    20,000-line core Directory.yml), so safe to do unconditionally for every
    test in the suite -- a test that sets ``VERAIN_PLUGIN_PATH`` would
    otherwise leak its discovered plugin into every test that runs after it.
    """
    PluginRegistry.reset_cache()
    yield
    PluginRegistry.reset_cache()


@pytest.fixture
def reset_directory_cache():
    """Drop the merged-``DirectoryProcessor`` cache around a test.

    NOT autouse: rebuilding it means re-parsing core Directory.yml (~1s), so
    only tests that actually change plugin discovery inputs and then go on
    to construct an ``InputParser``/``XMLGenerator`` should request this --
    applying it to the whole suite turns a one-time parse into hundreds of
    them.
    """
    reset_directory_processor_cache()
    yield
    reset_directory_processor_cache()
