from __future__ import annotations


def test_ingest_package_imports():
    import forwardflow.ingest as ingest
    assert ingest is not None


def test_feature_flag_enabled_phase1():
    from forwardflow.ingest.config import FF_INGEST_ENABLED
    assert FF_INGEST_ENABLED is True


def test_api_contracts_import():
    from forwardflow.ingest.api import interfaces, models, events, registry, errors  # noqa: F401


def test_engine_stubs_import():
    from forwardflow.ingest.engines.python_engine import PythonCopyEngine  # noqa: F401
    from forwardflow.ingest.engines.native_engine import NativeEngine  # noqa: F401
    from forwardflow.ingest.engines.os_engine import OsToolEngine  # noqa: F401


def test_pipeline_stubs_import():
    from forwardflow.ingest.pipeline import scheduler, probes, verify, reporter  # noqa: F401


def test_metadata_stubs_import():
    from forwardflow.ingest.metadata import base, quicktime  # noqa: F401
    from forwardflow.ingest.metadata.vendors import arri, red, sony, braw  # noqa: F401


def test_policy_stub_import():
    from forwardflow.ingest.policies.simple_policy import SimplePolicy  # noqa: F401


def test_ui_stubs_import():
    from forwardflow.ingest.ui.ingest_vm import IngestViewModel  # noqa: F401
    from forwardflow.ingest.ui.ingest_tab import build_ingest_tab  # noqa: F401


