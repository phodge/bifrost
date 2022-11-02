import os
import shutil
from pathlib import Path
from subprocess import run
from textwrap import dedent
from typing import List, Union

from paradox.output import Script

from tests.demo_service import DEMO_SERVICE_ROOT

CLIENT_TEMPLATES_PATH = Path(__file__).parent / 'client_templates'


def run_php_demo(
    script: Union[str, Script],
    *,
    root: Path,
    demo_service_port: int,
) -> None:
    demo_php = root / 'demo.php'
    if isinstance(script, Script):
        script.write_to_path(demo_php, lang='php')
    else:
        demo_php.write_text(dedent(script).lstrip())

    run(
        ['php', '-d', 'assert.exception=1', 'demo.php'],
        check=True,
        cwd=root,
        env=dict(
            **os.environ,
            DEMO_SERVICE_PORT=str(demo_service_port),
        ),
    )


def run_python_demo(
    script: Union[str, Script],
    *,
    root: Path,
    demo_service_port: int,
) -> None:
    demo_py = root / 'demo.py'
    if isinstance(script, Script):
        script.write_to_path(demo_py, lang='python')
    else:
        demo_py.write_text(dedent(script))

    run(
        ['python3', demo_py.name],
        check=True,
        cwd=root,
        env=dict(
            **os.environ,
            DEMO_SERVICE_PORT=str(demo_service_port),
            PYTHONPATH=CLIENT_TEMPLATES_PATH,
        ),
    )


def run_typescript_demo(
    script: str,
    *,
    root: Path,
    demo_service_port: int,
) -> None:
    demo_ts = root / 'demo.ts'
    demo_ts.write_text(dedent(script))

    # first we need to install Node libs (typescript etc)
    for filename in ['tsconfig.json', 'package.json', 'package-lock.json', 'assertlib.ts']:
        shutil.copy(
            DEMO_SERVICE_ROOT / 'client_templates' / filename,
            root / filename,
        )
    run(['npm', 'install'], check=True, cwd=root)

    # next we need to compile the source files
    buildpath = root / 'build'
    npxcmd: List[Union[str, os.PathLike[str]]] = [
        'npx',
        'tsc',
        '--outDir', buildpath,
        # needed for use of Promise<T>
        # XXX: adding 'DOM' to prevent complaints about fetch API being missing
        '--lib', 'ES2015,DOM',
        # for execution with vanilla Node
        '--module', 'commonjs',
    ]
    run(npxcmd, check=True, cwd=root)

    # finally we can run the generated demo script
    run(
        ['node', buildpath / 'demo.js'],
        check=True,
        cwd=buildpath,
        env=dict(**os.environ, DEMO_SERVICE_PORT=str(demo_service_port)),
    )
