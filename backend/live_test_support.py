from __future__ import annotations

from collections.abc import Mapping


def resolve_live_test_skip_reason(
    env: Mapping[str, str],
    *,
    config_exists: bool,
) -> str | None:
    run_live_tests = env.get("DEERFLOW_RUN_LIVE_TESTS") == "1"

    if not config_exists:
        return "No config.yaml found - live tests require valid API credentials"

    if env.get("CI") and not run_live_tests:
        return "Live tests skipped in CI unless DEERFLOW_RUN_LIVE_TESTS=1"

    if env.get("GITHUB_ACTIONS") and not run_live_tests:
        return "Live tests skipped in GitHub Actions unless DEERFLOW_RUN_LIVE_TESTS=1"

    if not run_live_tests:
        return "Live tests are opt-in; set DEERFLOW_RUN_LIVE_TESTS=1 to run them"

    return None
