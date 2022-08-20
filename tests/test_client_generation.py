import os
from os.path import dirname
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

import pytest


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
            f'''
            from get_client import get_client

            t = get_client()
            rev = t.get_reversed("Hello world")
            assert rev == "dlrow olleH"
            '''
        )
        demo_path.write_text(demo_script)

        run(
            ['python', demo_path.name],
            check=True,
            cwd=tmpdir,
            env=dict(
                **os.environ,
                DEMO_SERVICE_PORT=str(demo_service_port),
                PYTHONPATH=dirname(__file__) + '/demo_service/client_templates',
            ),
        )
