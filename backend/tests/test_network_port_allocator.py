"""Regression tests for sandbox port allocation."""

from __future__ import annotations

import socket

from deerflow.utils.network import PortAllocator


def test_port_allocator_skips_port_bound_on_loopback():
    """Ports already bound on 127.0.0.1 should not be reallocated."""
    allocator = PortAllocator()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        occupied_port = listener.getsockname()[1]

        allocated_port = allocator.allocate(start_port=occupied_port, max_range=5)
        try:
            assert allocated_port != occupied_port
        finally:
            allocator.release(allocated_port)
