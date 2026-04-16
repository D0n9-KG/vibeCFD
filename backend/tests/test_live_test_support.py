from live_test_support import resolve_live_test_skip_reason


def test_live_tests_skip_by_default_even_when_config_exists() -> None:
    reason = resolve_live_test_skip_reason({}, config_exists=True)

    assert reason is not None
    assert "DEERFLOW_RUN_LIVE_TESTS=1" in reason


def test_live_tests_skip_in_ci_without_explicit_opt_in() -> None:
    reason = resolve_live_test_skip_reason({"CI": "true"}, config_exists=True)

    assert reason is not None
    assert "CI" in reason


def test_live_tests_can_run_when_explicitly_opted_in() -> None:
    reason = resolve_live_test_skip_reason(
        {"DEERFLOW_RUN_LIVE_TESTS": "1"},
        config_exists=True,
    )

    assert reason is None


def test_live_tests_require_config_even_when_explicitly_opted_in() -> None:
    reason = resolve_live_test_skip_reason(
        {"DEERFLOW_RUN_LIVE_TESTS": "1"},
        config_exists=False,
    )

    assert reason is not None
    assert "config.yaml" in reason
