from pathlib import Path

import pytest

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
