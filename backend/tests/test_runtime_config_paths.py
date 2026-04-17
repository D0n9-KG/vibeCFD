from pathlib import Path
from types import SimpleNamespace


def _raise_on_resolve(self, *args, **kwargs):  # pragma: no cover - helper for regression tests
    raise AssertionError("Path.resolve should not be used in runtime config path helpers")


def test_runtime_config_override_path_resolution_avoids_path_resolve(
    monkeypatch,
    tmp_path: Path,
):
    import importlib

    runtime_config = importlib.import_module(
        "deerflow.config.runtime_config_overrides"
    )

    monkeypatch.setattr(Path, "resolve", _raise_on_resolve, raising=False)
    monkeypatch.setattr(
        runtime_config,
        "get_paths",
        lambda: SimpleNamespace(
            base_dir=tmp_path,
            runtime_config_overrides_file=tmp_path / "runtime-config.json",
        ),
    )

    assert runtime_config.RuntimeConfigOverrides.resolve_config_path() == (
        tmp_path / "runtime-config.json"
    )


def test_runtime_model_registry_path_resolution_avoids_path_resolve(
    monkeypatch,
    tmp_path: Path,
):
    import importlib

    runtime_models = importlib.import_module("deerflow.config.runtime_models")

    monkeypatch.setattr(Path, "resolve", _raise_on_resolve, raising=False)
    monkeypatch.setattr(
        runtime_models,
        "get_paths",
        lambda: SimpleNamespace(
            base_dir=tmp_path,
            runtime_models_file=tmp_path / "runtime-models.json",
            runtime_model_secrets_file=tmp_path / "runtime-model-secrets.json",
        ),
    )

    assert runtime_models.RuntimeModelRegistry.resolve_config_path() == (
        tmp_path / "runtime-models.json"
    )
    assert runtime_models.RuntimeModelSecrets.resolve_config_path() == (
        tmp_path / "runtime-model-secrets.json"
    )
