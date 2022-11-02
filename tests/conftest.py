import random
import time
from dataclasses import dataclass
from os.path import dirname
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Iterator, Literal, Tuple, Union, cast

import pytest
from paradox.output import Script

from tests.demo_service.execute import run_php_demo, run_python_demo
from tests.demo_service.generate import (
    generate_demo_service_php_client, generate_demo_service_python_client,
    generate_demo_service_typescript_client)


@pytest.fixture
def demo_service() -> Iterator[Any]:
    from .demo_service import service

    yield service


@pytest.fixture(scope='function')
def tmppath() -> Iterable[Path]:
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@dataclass
class DemoRunner:
    lang: Literal['php', 'python', 'typescript']
    flavour: Literal['abstract', 'curl', 'requests']
    where: Path
    demo_service_port: int

    def run_demo(self, demo_script: Union[str, Script]) -> None:
        if self.lang == 'php':
            generate_demo_service_php_client(self.where, flavour=self.flavour)
            run_php_demo(demo_script, root=self.where, demo_service_port=self.demo_service_port)
        elif self.lang == 'python':
            generate_demo_service_python_client(self.where, flavour=self.flavour)
            run_python_demo(demo_script, root=self.where, demo_service_port=self.demo_service_port)
        elif self.lang == 'typescript':
            generate_demo_service_typescript_client(self.where, flavour=self.flavour)
            raise NotImplementedError("TODO: finish this")
        else:
            raise Exception(f"Unexpected lang {self.lang!r}")


def lang_flavour(request: Any) -> Iterable[Tuple[str, str]]:
    parts = request.param.split('/')
    yield parts[0], parts[1]


@pytest.fixture(params=[
    'python/abstract',
    'python/requests',
    'php/abstract',
    # TODO: generate and add unit tests for a php/curl client
    # 'php/curl',
    'typescript/abstract',
    'typescript/fetch',
])
def demo_runner(
    request: Any,
    tmppath: Path,  # pylint: disable=redefined-outer-name
    demo_service_port: int,  # pylint: disable=redefined-outer-name
) -> Iterable[DemoRunner]:
    lang, flavour = request.param.split('/')

    yield DemoRunner(
        cast(Any, lang),
        cast(Any, flavour),
        where=tmppath,
        demo_service_port=demo_service_port,
    )


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
        time.sleep(0.2)
        yield port
    finally:
        if p:
            p.kill()
