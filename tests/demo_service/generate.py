import shutil
from pathlib import Path
from textwrap import dedent

from tests.demo_service import DEMO_SERVICE_ROOT, service


def generate_demo_service_php_client(
    root: Path,
    *,
    flavour: str,
) -> None:
    """
    Generates a generated_client.php module and a get_client.php
    """
    generated_client_path = root / 'generated_client.php'
    get_client_path = root / 'get_client.php'

    if flavour == 'abstract':
        service.generatePHPClient(generated_client_path, 'ClientBase', flavour='abstract')
        # install our get_client.php helper module
        shutil.copy(
                DEMO_SERVICE_ROOT / 'client_templates' / 'demo_curl_client.php',
                root / 'demo_curl_client.php'
                )
        get_client_script = '''
            <?php

            require 'generated_client.php';
            require 'demo_curl_client.php';

            function get_client() {
                return new DemoCurlClient('127.0.0.1', intval(getenv('DEMO_SERVICE_PORT')));
            }
            '''
    else:
        raise Exception(f"Unexpected flavour {flavour!r}")

    # write out the get_client script
    get_client_path.write_text(dedent(get_client_script).lstrip())


def generate_demo_service_python_client(
    root: Path,
    *,
    flavour: str,
) -> None:
    """
    Generates a generated_client.py module and a get_client.py
    """
    generated_client_path = root / 'generated_client.py'
    get_client_path = root / 'get_client.py'

    if flavour == 'abstract':
        service.generatePythonClient(
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
        service.generatePythonClient(
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


def generate_demo_service_typescript_client(
    root: Path,
    *,
    flavour: str,
) -> None:
    """
    Generates a generated_client.ts module and a get_client.ts
    """
    generated_client_path = root / 'generated_client.ts'
    get_client_path = root / 'get_client.ts'

    if flavour == 'abstract':
        service.generateTypescriptWebClient(
            generated_client_path,
            'ClientBase',
            flavour='abstract',
            npmroot=root,
        )
        # we need to install our Node HTTP client into the tmp folder
        shutil.copy(
            DEMO_SERVICE_ROOT / 'client_templates' / 'demo_fetch_client.ts',
            root / 'demo_fetch_client.ts'
        )
        get_client_script = dedent(
            '''
            import {DemoClient} from './demo_fetch_client';

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
