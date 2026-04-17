import importlib


def test_build_environment_fingerprint_falls_back_when_config_is_missing(
    tmp_path,
    monkeypatch,
):
    environment_parity = importlib.import_module("deerflow.domain.submarine.environment_parity")

    monkeypatch.delenv("DEER_FLOW_RUNTIME_PROFILE", raising=False)
    monkeypatch.delenv("DEER_FLOW_DOCKER_SOCKET", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOME", raising=False)
    monkeypatch.delenv("DEER_FLOW_ROOT", raising=False)
    monkeypatch.delenv("DEER_FLOW_REPO_ROOT", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_BASE_DIR", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_SKILLS_PATH", raising=False)
    monkeypatch.setattr(
        environment_parity,
        "get_app_config",
        lambda: (_ for _ in ()).throw(FileNotFoundError("config missing in CI")),
    )
    monkeypatch.setattr(
        environment_parity.AppConfig,
        "resolve_config_path",
        classmethod(
            lambda cls: (_ for _ in ()).throw(
                FileNotFoundError("config path missing in CI"),
            ),
        ),
    )

    fingerprint = environment_parity.build_environment_fingerprint(
        workspace_dir=tmp_path / "workspace",
        outputs_dir=tmp_path / "outputs",
    )

    assert fingerprint.profile_id == "local_cli"
    assert fingerprint.runtime_origin == "unit_test"
    assert fingerprint.host_mount_strategy == "workspace_path"
    assert fingerprint.sandbox_image is None
    assert fingerprint.config_sources == ["default:local_cli"]


def test_build_environment_parity_assessment_keeps_configless_unit_test_runnable(
    tmp_path,
    monkeypatch,
):
    environment_parity = importlib.import_module("deerflow.domain.submarine.environment_parity")

    monkeypatch.delenv("DEER_FLOW_RUNTIME_PROFILE", raising=False)
    monkeypatch.delenv("DEER_FLOW_DOCKER_SOCKET", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOME", raising=False)
    monkeypatch.delenv("DEER_FLOW_ROOT", raising=False)
    monkeypatch.delenv("DEER_FLOW_REPO_ROOT", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_BASE_DIR", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_SKILLS_PATH", raising=False)
    monkeypatch.setattr(
        environment_parity,
        "get_app_config",
        lambda: (_ for _ in ()).throw(FileNotFoundError("config missing in CI")),
    )
    monkeypatch.setattr(
        environment_parity.AppConfig,
        "resolve_config_path",
        classmethod(
            lambda cls: (_ for _ in ()).throw(
                FileNotFoundError("config path missing in CI"),
            ),
        ),
    )

    fingerprint = environment_parity.build_environment_fingerprint(
        workspace_dir=tmp_path / "workspace",
        outputs_dir=tmp_path / "outputs",
    )
    assessment = environment_parity.build_environment_parity_assessment(fingerprint)

    assert assessment.parity_status == "matched"
    assert assessment.drift_reasons == []


def test_build_environment_parity_assessment_marks_configless_docker_profile_as_drifted_not_blocked(
    tmp_path,
    monkeypatch,
):
    environment_parity = importlib.import_module("deerflow.domain.submarine.environment_parity")

    fake_socket = tmp_path / "fake-docker.sock"
    fake_socket.write_text("", encoding="utf-8")

    monkeypatch.setenv("DEER_FLOW_RUNTIME_PROFILE", "docker_compose_dev")
    monkeypatch.setenv("DEER_FLOW_DOCKER_SOCKET", str(fake_socket))
    monkeypatch.delenv("DEER_FLOW_HOME", raising=False)
    monkeypatch.delenv("DEER_FLOW_ROOT", raising=False)
    monkeypatch.delenv("DEER_FLOW_REPO_ROOT", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_BASE_DIR", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_SKILLS_PATH", raising=False)
    monkeypatch.setattr(
        environment_parity,
        "get_app_config",
        lambda: (_ for _ in ()).throw(FileNotFoundError("config missing in CI")),
    )
    monkeypatch.setattr(
        environment_parity.AppConfig,
        "resolve_config_path",
        classmethod(
            lambda cls: (_ for _ in ()).throw(
                FileNotFoundError("config path missing in CI"),
            ),
        ),
    )

    fingerprint = environment_parity.build_environment_fingerprint(
        workspace_dir=tmp_path / "workspace",
        outputs_dir=tmp_path / "outputs",
    )
    assessment = environment_parity.build_environment_parity_assessment(fingerprint)

    assert assessment.parity_status == "drifted_but_runnable"
    assert any("Host mount strategy" in item for item in assessment.drift_reasons)
    assert not any("Sandbox image is missing" in item for item in assessment.drift_reasons)
