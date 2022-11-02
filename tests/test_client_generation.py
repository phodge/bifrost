import os
import shutil
from os.path import dirname
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any, Iterable, List, Union

import pytest

DEMO_SERVICE_ROOT = Path(__file__).parent / 'demo_service'


def _run_php(script: str, **kwargs: Any) -> None:
    cmd = ['php', '-d', 'assert.exception=1', script]
    run(cmd, **kwargs, check=True)


@pytest.fixture(scope='function')
def tmppath() -> Iterable[Path]:
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.parametrize('flavour', ['abstract'])
def test_generate_php_client(flavour: str, demo_service: Any, demo_service_port: int) -> None:
    with TemporaryDirectory() as tmpdir:
        clientpath = Path(tmpdir) / 'test_client.php'

        if flavour == 'abstract':
            demo_service.generatePHPClient(clientpath, 'TestClient', flavour='abstract')
            # install our get_client.php helper module
            shutil.copy(
                    DEMO_SERVICE_ROOT / 'client_templates' / 'demo_curl_client.php',
                    Path(tmpdir) / 'demo_curl_client.php'
                    )
        else:
            raise Exception(f"Unexpected flavour {flavour!r}")

        demo_script = dedent(
            '''
            <?php

            require 'test_client.php';

            require 'demo_curl_client.php';

            $service = new DemoCurlClient();
            $rev = $service->get_reversed("Hello world");
            assert($rev === "dlrow olleH");

            $pets = $service->get_pets();
            assert(is_array($pets));
            assert(count($pets) === 2);
            assert($pets[0] instanceof Pet);
            assert($pets[1] instanceof Pet);
            assert($pets[0]->name === "Basil");
            assert($pets[1]->name === "Billy");

            $check = $service->check_pets(['basil' => $pets[0], 'billy' => $pets[1]]);
            assert($check === 'pets_ok!');
            '''
        )
        demo_path = Path(tmpdir) / 'demo.php'
        demo_path.write_text(demo_script)

        run(
            ['php', '-d', 'assert.exception=1', 'demo.php'],
            check=True,
            cwd=tmpdir,
            env=dict(
                **os.environ,
                DEMO_SERVICE_PORT=str(demo_service_port),
            ),
        )


@pytest.mark.parametrize('flavour', ['abstract', 'requests'])
def test_generate_python_client(flavour: str, demo_service: Any, demo_service_port: int) -> None:
    with TemporaryDirectory() as tmpdir:
        generated_client_path = Path(tmpdir) / 'generated_client.py'
        get_client_path = Path(tmpdir) / 'get_client.py'
        demo_path = Path(tmpdir) / 'checker.py'

        if flavour == 'abstract':
            demo_service.generatePythonClient(
                generated_client_path,
                'ClientBase',
                flavour='abstract',
            )
            get_client_script = dedent(
                '''
                from requestsclient import RequestsPythonClient
                def get_client():
                    return RequestsPythonClient()
                '''
            )
        else:
            assert flavour == 'requests'
            demo_service.generatePythonClient(
                generated_client_path,
                'GeneratedRequestsClient',
                flavour='requests',
            )
            get_client_script = dedent(
                '''
                import os
                from generated_client import GeneratedRequestsClient
                def get_client():
                    return GeneratedRequestsClient(
                        host='127.0.0.1',
                        port=int(os.environ['DEMO_SERVICE_PORT']),
                    )
                '''
            )

        # write out the get_client script
        get_client_path.write_text(get_client_script)

        demo_script = dedent(
            '''
            from get_client import get_client
            from generated_client import Pet

            t = get_client()
            rev = t.get_reversed("Hello world")
            assert rev == "dlrow olleH"

            pets = t.get_pets()
            assert isinstance(pets, list)
            assert len(pets) == 2
            assert isinstance(pets[0], Pet)
            assert isinstance(pets[1], Pet)
            assert pets[0].name == "Basil"
            assert pets[1].name == "Billy"

            # TODO: we can't pass dataclasses as args yet in python because python doesn't
            # automatically json-encode dataclasses
            # check = t.check_pets({'basil': pets[0], 'billy': pets[1]})
            # assert check == 'pets_ok!'
            '''
        )
        demo_path.write_text(demo_script)

        run(
            ['python3', demo_path.name],
            check=True,
            cwd=tmpdir,
            env=dict(
                **os.environ,
                DEMO_SERVICE_PORT=str(demo_service_port),
                PYTHONPATH=dirname(__file__) + '/demo_service/client_templates',
            ),
        )


@pytest.mark.parametrize('flavour', ['abstract'])
def test_generate_typescript_client(
    flavour: str,
    demo_service: Any,
    demo_service_port: int,
    tmppath: Path,
) -> None:
    get_client_path = tmppath / 'get_client.ts'

    if flavour == 'abstract':
        demo_service.generateTypescriptWebClient(
            tmppath / 'generated_methods.ts',
            'ClientBase',
            flavour='abstract',
            npmroot=tmppath,
        )
        # we need to install our Node HTTP client into the tmp folder
        shutil.copy(
            DEMO_SERVICE_ROOT / 'client_templates' / 'demo_HTTP_client.ts',
            tmppath / 'demo_HTTP_client.ts'
        )
        get_client_script = dedent(
            '''
            import {DemoClient} from './demo_HTTP_client';

            export function get_client() {
                const port: string|undefined = process.env.DEMO_SERVICE_PORT;
                if (port === undefined || port === '') {
                    throw new Error("$DEMO_SERVICE_PORT is empty");
                }
                return new DemoClient('127.0.0.1', parseInt(port, 10));
            }
            '''
        )
    else:
        raise Exception(f"Unexpected flavour {flavour!r}")

    # write out the get_client script
    get_client_path.write_text(get_client_script)

    demo_script = dedent(
        '''
        import {get_client} from './get_client';
        import {Pet, ClientBase} from './generated_methods';
        import {ApiFailure} from './generated_methods';
        import {assert_eq, assert_islist} from './assertlib';

        // NOTE: we need to wrap the assertions in an async function because CommonJS format
        // doesn't permit await at the top level
        (async () => {
            let c: ClientBase = get_client();
            const rev = await c.get_reversed("Hello world");
            assert_eq(rev, "dlrow olleH");

            const pets = await c.get_pets()
            assert_islist(pets, 2);
            assert_eq(pets[0].name, "Basil");
            assert_eq(pets[1].name, "Billy");

            const check = await c.check_pets({'basil': pets[0], 'billy': pets[1]})
            assert_eq(check, 'pets_ok!');
        })();
        '''
    )
    (tmppath / 'demo.ts').write_text(demo_script)

    # first we need to install Node libs (typescript etc)
    for filename in ['tsconfig.json', 'package.json', 'package-lock.json', 'assertlib.ts']:
        shutil.copy(
            DEMO_SERVICE_ROOT / 'client_templates' / filename,
            tmppath / filename,
        )
    run(['npm', 'install'], check=True, cwd=tmppath)

    # next we need to compile the source files
    buildpath = tmppath / 'build'
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
    run(npxcmd, check=True, cwd=tmppath)

    # finally we can run the generated demo script
    run(
        ['node', buildpath / 'demo.js'],
        check=True,
        cwd=buildpath,
        env=dict(**os.environ, DEMO_SERVICE_PORT=str(demo_service_port)),
    )
