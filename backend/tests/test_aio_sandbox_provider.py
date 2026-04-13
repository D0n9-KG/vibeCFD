from __future__ import annotations

import threading
import time
from types import SimpleNamespace


def test_aio_sandbox_execute_command_toggles_busy_callbacks(monkeypatch):
    sandbox_module = __import__(
        "deerflow.community.aio_sandbox.aio_sandbox",
        fromlist=["AioSandbox"],
    )

    class _FakeShell:
        def exec_command(self, command: str):
            assert command == "echo hello"
            return SimpleNamespace(data=SimpleNamespace(output="hello"))

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            self.shell = _FakeShell()

    monkeypatch.setattr(sandbox_module, "AioSandboxClient", _FakeClient)

    events: list[tuple[str, str]] = []
    sandbox = sandbox_module.AioSandbox(
        id="busy-box",
        base_url="http://sandbox.local",
        on_command_start=lambda sandbox_id: events.append(("start", sandbox_id)),
        on_command_end=lambda sandbox_id: events.append(("end", sandbox_id)),
    )

    assert sandbox.execute_command("echo hello") == "hello"
    assert events == [("start", "busy-box"), ("end", "busy-box")]


def test_aio_sandbox_provider_cleanup_skips_busy_sandboxes():
    provider_module = __import__(
        "deerflow.community.aio_sandbox.aio_sandbox_provider",
        fromlist=["AioSandboxProvider"],
    )

    provider = object.__new__(provider_module.AioSandboxProvider)
    provider._lock = threading.Lock()
    provider._last_activity = {"busy-box": time.time() - 1000}
    provider._warm_pool = {}
    provider._busy_sandboxes = {"busy-box"}
    provider._sandboxes = {"busy-box": object()}
    provider._sandbox_infos = {}
    provider._thread_sandboxes = {}

    destroyed: list[str] = []
    provider.destroy = lambda sandbox_id: destroyed.append(sandbox_id)

    provider._cleanup_idle_sandboxes(idle_timeout=1)

    assert destroyed == []
