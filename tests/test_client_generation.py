from pathlib import Path
from tests.scenarios import assert_contains_text, assert_eq, assert_isinstance

import pytest
from paradox.expressions import PanCall, pan
from paradox.generate.statements import HardCodedStatement
from paradox.output import Script

from tests.conftest import DemoRunner
from tests.demo_service.execute import (run_php_demo, run_python_demo,
                                        run_typescript_demo)
from tests.demo_service.generate import (
    generate_demo_service_php_client, generate_demo_service_python_client,
    generate_demo_service_typescript_client)

DEMO_SERVICE_ROOT = Path(__file__).parent / 'demo_service'


@pytest.mark.parametrize('flavour', ['abstract'])
def test_generate_php_client(
    flavour: str,
    tmppath: Path,
    demo_service_port: int,
) -> None:
    generate_demo_service_php_client(tmppath, flavour=flavour)

    demo_script = '''
        <?php

        require 'get_client.php';

        $service = get_client();
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

    run_php_demo(demo_script, root=tmppath, demo_service_port=demo_service_port)


@pytest.mark.parametrize('flavour', ['abstract', 'requests'])
def test_generate_python_client(
    flavour: str,
    tmppath: Path,
    demo_service_port: int,
) -> None:
    generate_demo_service_python_client(tmppath, flavour=flavour)

    demo_script = '''
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

    run_python_demo(demo_script, root=tmppath, demo_service_port=demo_service_port)


@pytest.mark.parametrize('flavour', ['abstract'])
def test_generate_typescript_client(
    flavour: str,
    demo_service_port: int,
    tmppath: Path,
) -> None:
    generate_demo_service_typescript_client(tmppath, flavour=flavour)

    demo_script = '''
        import {get_client} from './get_client';
        import {Pet, ClientBase} from './generated_client';
        import {ApiFailure} from './generated_client';
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

    run_typescript_demo(demo_script, root=tmppath, demo_service_port=demo_service_port)


def test_generated_client_session_auth(demo_runner: DemoRunner) -> None:
    if demo_runner.lang == 'typescript':
        # XXX: Typescript test isn't strictly necessary here as browsers will support sessions by
        # default
        return

    if demo_runner.lang not in ('python', 'php'):
        raise Exception(f"Unexpected lang {demo_runner.lang!r}")

    s = Script()

    s.also(HardCodedStatement(
        php='require "get_client.php";',
        python=None,
    ))

    s.remark('load the client')
    s.alsoImportPy('get_client', ['get_client'])
    v_client = s.alsoDeclare('v_client', 'no_type', PanCall('get_client'))

    s.remark('should return an ApiUnauthorized first')
    s.alsoImportPy('generated_client', ['ApiUnauthorized'])
    v_result = s.alsoDeclare('result', 'no_type', PanCall(v_client.getprop('whoami')))
    s.also(HardCodedStatement(
        php='var_export($result);',
        python=None,
    ))
    assert_isinstance(s, v_result, 'ApiUnauthorized')
    assert_contains_text(s, v_result.getprop('message'), 'Not logged in')

    s.remark('try an invalid username/password')
    assert_eq(
        s,
        PanCall(v_client.getprop('login'), pan("MrAnderson"), pan("secr3t")),
        'Invalid username or password',
    )

    s.remark('try missing credentials')
    assert_eq(
        s,
        PanCall(v_client.getprop('login'), pan(""), pan("secr3t")),
        'Username was empty',
    )

    s.remark('confirm still not logged in')
    s.alsoAssign(v_result, PanCall(v_client.getprop('whoami')))
    assert_isinstance(s, v_result, 'ApiUnauthorized')
    assert_contains_text(s, v_result.getprop('message'), 'Not logged in')

    s.remark('now log in with correct credentials')
    assert_eq(
        s,
        PanCall(v_client.getprop('login'), pan("neo"), pan("trinity")),
        pan(True),
    )
    assert_eq(
        s,
        PanCall(v_client.getprop('whoami')),
        pan('the_one'),
    )

    demo_runner.run_demo(s)
