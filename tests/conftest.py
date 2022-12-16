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

from tests.demo_service.testutils import (
    generate_demo_service_php_client, generate_demo_service_python_client,
    generate_demo_service_typescript_client, run_php_demo, run_python_demo,
    run_python_typecheck, run_typescript_demo)


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
    errors: Literal['return', 'raise']
    where: Path
    demo_service_port: int

    def run_demo(self, demo_script: Union[str, Script]) -> None:
        if self.lang == 'php':
            generate_demo_service_php_client(
                self.where,
                flavour=self.flavour,
                on_error=self.errors,
            )
            run_php_demo(
                demo_script,
                root=self.where,
                demo_service_port=self.demo_service_port,
                on_error=self.errors,
            )
        elif self.lang == 'python':
            assert self.errors == 'return'
            generate_demo_service_python_client(self.where, flavour=self.flavour)
            run_python_demo(demo_script, root=self.where, demo_service_port=self.demo_service_port)
            # we also want to run mypy over the project
            run_python_typecheck(self.where)
        elif self.lang == 'typescript':
            assert self.errors == 'return'
            generate_demo_service_typescript_client(self.where, flavour=self.flavour)
            run_typescript_demo(
                demo_script,
                root=self.where,
                demo_service_port=self.demo_service_port,
            )
        else:
            raise Exception(f"Unexpected lang {self.lang!r}")


def lang_flavour(request: Any) -> Iterable[Tuple[str, str]]:
    parts = request.param.split('/')
    yield parts[0], parts[1]


@pytest.fixture(params=[
    'python/abstract/return',
    'python/requests/return',
    'php/abstract/return',
    'php/abstract/raise',
    # TODO: generate and add unit tests for a php/curl client
    # 'php/curl',
    'typescript/abstract/return',
    'typescript/fetch/return',
])
def demo_runner(
    request: Any,
    tmppath: Path,  # pylint: disable=redefined-outer-name
    demo_service_port: int,  # pylint: disable=redefined-outer-name
) -> Iterable[DemoRunner]:
    lang, flavour, errors = request.param.split('/')

    yield DemoRunner(
        cast(Any, lang),
        cast(Any, flavour),
        cast(Any, errors),
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
        time.sleep(0.3)
        yield port
    finally:
        if p:
            p.kill()
