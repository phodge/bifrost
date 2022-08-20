import random
from os.path import dirname
from subprocess import Popen
from typing import Any, Iterator

import pytest


@pytest.fixture
def demo_service() -> Iterator[Any]:
    from .demo_service import service

    yield service


@pytest.fixture
def demo_service_port() -> Iterator[int]:
    """Spins up the DemoService and exposes it on random port."""
    port = random.randint(5000, 9999)

    p = None

    cmd = ['flask', '--app', 'demo_service', 'run', '-p', str(port)]

    try:
        p = Popen(cmd, cwd=dirname(__file__))

        # TODO: do we need a mechanism to wait for the Flask service to become available before we
        # start executing the test?
        yield port
    finally:
        if p:
            p.kill()
