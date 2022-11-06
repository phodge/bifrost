from pathlib import Path

import pytest
from paradox.expressions import PanCall, PanDict, pan
from paradox.generate.statements import HardCodedStatement
from paradox.output import Script
from paradox.typing import CrossAny, CrossStr

from tests.conftest import DemoRunner
from tests.demo_service.execute import run_typescript_demo
from tests.demo_service.generate import generate_demo_service_typescript_client
from tests.scenarios import (assert_contains_text, assert_eq,
                             assert_isinstance, assert_islist)

DEMO_SERVICE_ROOT = Path(__file__).parent / 'demo_service'


def test_generated_client(
    demo_runner: DemoRunner,
) -> None:
    if demo_runner.lang not in ('php', 'python'):
        return

    s = Script()

    s.also(HardCodedStatement(
        php='require "get_client.php";',
        python=None,
    ))

    s.remark('load the client')
    s.alsoImportPy('get_client', ['get_client'])
    v_client = s.alsoDeclare('v_client', 'no_type', PanCall('get_client'))

    s.remark('simple string-reversal endpoint')
    assert_eq(
        s,
        PanCall(v_client.getprop('get_reversed'), pan("Hello world")),
        "dlrow olleH",
    )

    s.remark('method with a more complex return type')
    v_pets = s.alsoDeclare('pets', CrossAny(), PanCall(v_client.getprop('get_pets')))
    assert_islist(s, v_pets, size=2)
    s.alsoImportPy('generated_client', ['Pet'])
    assert_isinstance(s, v_pets.getindex(0), 'Pet')
    assert_isinstance(s, v_pets.getindex(1), 'Pet')
    assert_eq(s, v_pets.getindex(0).getprop('name'), 'Basil')
    assert_eq(s, v_pets.getindex(1).getprop('name'), 'Billy')

    s.remark('Testing a method that *receives* a complex argument type')
    if demo_runner.lang == 'python':
        s.remark("XXX: this is not yet supported in python")
        s.remark("TODO: we can't pass dataclasses as args yet in python because python")
        s.remark("doesn't automatically json-encode dataclasses")
    else:
        v_check_arg = PanDict({}, CrossStr(), CrossAny())
        v_check_arg.addPair(pan('basil'), v_pets.getindex(0))
        v_check_arg.addPair(pan('billy'), v_pets.getindex(1))
        v_check = s.alsoDeclare('check', 'no_type', PanCall(
            v_client.getprop('check_pets'),
            v_check_arg,
        ))
        assert_eq(s, v_check, 'pets_ok!')

    demo_runner.run_demo(s)


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


# TODO: also test
# - ApiBroken / ApiOutage
