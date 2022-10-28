from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import (Any, Callable, Iterable, List, Literal, Optional, Tuple,
                    Union)

import pytest
from paradox.expressions import PanExpr, PanVar, pan, pandict, panlist, phpexpr
from paradox.generate.statements import HardCodedStatement
from paradox.output import Script
from paradox.typing import CrossAny

from bifrostrpc.typing import NullTypeSpec, TypeSpec, UnionTypeSpec

from .scenarios import Scenario, json_obj_to_php, json_obj_to_python
from .scenarios.gadgets import (DEVICE0, DEVICE1, DEVICE2, GADGET0, GADGET1,
                                GIZMO0, MACHINE0, MACHINE1, MACHINE2, WIDGET0,
                                WIDGET1)
from .scenarios.pets import PET0, PET1
from .scenarios.travellers import TRAVELLER0, TRAVELLER1
from .scenarios.users import USER0, USER1


def _run_php(script: str, **kwargs: Any) -> None:
    cmd = ['php', '-d', 'assert.exception=1', script]
    run(cmd, **kwargs)


def _run_py(script: str, **kwargs: Any) -> None:
    run(['python', script], **kwargs)


@pytest.mark.parametrize('scenario', [
    USER0(),
    USER1(),
    PET0(),
    PET1(),
    TRAVELLER0(),
    TRAVELLER1(),
    GADGET0(),
    GADGET1(),
    GIZMO0(),
    WIDGET0(),
    WIDGET1(),
    DEVICE0(),
    DEVICE1(),
    DEVICE2(),
    MACHINE0(),
    MACHINE1(),
    MACHINE2(),
])
@pytest.mark.parametrize('lang', ['php', 'python'])
def test_get_dataclass_spec(
    scenario: Scenario,
    lang: Literal['php', 'python'],
) -> None:
    from bifrostrpc.generators.conversion import getDataclassSpec
    from bifrostrpc.typing import Advanced

    # load dataclasses
    adv = Advanced()
    for dc in scenario.dataclasses:
        adv.addDataclass(dc)

    classname = scenario.dataclasses[0].__name__

    s = Script()

    for dc in scenario.dataclasses:
        s.also(getDataclassSpec(dc, adv=adv, lang=lang, hoistcontext=s))

    s.also(HardCodedStatement(
        php=f'$VAR = {classname}::fromDict({json_obj_to_php(scenario.obj)}, "\\$_");',
        python=f'VAR = {classname}.fromDict({json_obj_to_python(scenario.obj)}, "DATA")',
    ))
    s.also(HardCodedStatement(
        php=f'assert($VAR instanceof {classname});',
        python=f'assert isinstance(VAR, {classname})',
    ))

    scenario.add_assertions(s, PanVar('VAR', CrossAny()))

    with TemporaryDirectory() as tmpdir:
        if lang == 'php':
            s.write_to_path(Path(tmpdir) / 'dataclass.php', lang=lang)
            _run_php('dataclass.php', cwd=tmpdir, check=True)
        elif lang == 'python':
            s.write_to_path(Path(tmpdir) / 'dataclass.py', lang=lang)
            _run_py('dataclass.py', cwd=tmpdir, check=True)
        else:
            raise Exception(f"Unexpected lang {lang!r}")


# a filter block isn't possible for these input types using PHP
@pytest.mark.parametrize('input_type', [
    Optional[List[str]],
    Union[List[str], List[int]],
])
def test_get_filter_block_php_not_possible(input_type: Any) -> None:
    from bifrostrpc.generators import Names
    from bifrostrpc.generators.conversion import (FilterNotPossible,
                                                  getFilterBlock)
    from bifrostrpc.typing import Advanced, getTypeSpec

    typespec = getTypeSpec(input_type, adv=Advanced())
    with pytest.raises(FilterNotPossible):
        getFilterBlock(
            PanVar('TEST_INPUT', CrossAny()),
            '$TEST_INPUT',
            spec=typespec,
            names=Names(),
            lang='php',
        )


PHP_INPUTS: Iterable[Tuple[Any, List[Any], List[Any], bool]] = [
        (
            str,
            ['', 'hello'],
            [False, True, 5, 5.5, [], ['hello'], {}, {'message': 'hello'}],
            True,
        ),
        (
            int,
            [-5, 0, 5],
            [False, True, 5.5, 5.0, '', 'stringval', [], ['hello'], {}, {'message': 'hello'}],
            True,
        ),
        (
            bool,
            [True, False],
            [5.5, 5.0, '', 'stringval', [], ['hello'], {}, {'message': 'hello'}],
            True,
        ),
        # TODO: refactor this to a single Literal with 3 possible values
        (
            Union[Literal[2], Literal[4], Literal[6]],
            [2, 4, 6],
            [False, True, 0, 5, 5.5, [], ['hello'], [2], {}, {'number': 2}],
            True,
        ),
        # and now List[T]
        (
            List[str],
            [[], [''], ['test', 'True', '5']],
            [None],
            False,
        ),
]


def parametrize(
    fn: Callable[..., None],
) -> Callable[..., None]:
    from bifrostrpc.typing import Advanced, getTypeSpec

    adv = Advanced()
    inputs = []
    for target_type, valid_values, invalid_values, attempt_optional in PHP_INPUTS:
        typespec = getTypeSpec(target_type, adv=adv)
        for value in valid_values:
            inputs.append([typespec, value, True])
        for value in invalid_values:
            inputs.append([typespec, value, False])

        # null/None is not valid by default
        inputs.append([typespec, None, False])

        # make an Optional[...] version of the typespec where null/None is valid
        if attempt_optional:
            inputs.append([UnionTypeSpec([typespec, NullTypeSpec()]), None, True])

    return pytest.mark.parametrize('typespec,test_input,is_valid', inputs)(fn)


@parametrize
def test_get_filter_block_php(typespec: TypeSpec, test_input: Any, is_valid: bool) -> None:
    # TODO: this unit test might be pointless: all of this logic should have been covered by the
    # dataclass-converter-generator unit tests above. We should try and measure code coverage and
    # remove this test if it isn't covering any additional code.
    if isinstance(test_input, float):
        # TODO: add support for floating point values
        return

    pan_input: PanExpr

    if isinstance(test_input, list):
        pan_input = panlist(test_input, CrossAny())
    elif isinstance(test_input, dict):
        pan_input = pandict(test_input, CrossAny())
    else:
        pan_input = pan(test_input)

    from bifrostrpc.generators import Names
    from bifrostrpc.generators.conversion import getFilterBlock

    v_input = PanVar('TEST_INPUT', CrossAny())

    s = Script()
    s.alsoAssign(v_input, pan_input)
    s.alsoAssign(PanVar('is_valid', CrossAny()), pan(is_valid))

    names = Names()
    stmt = getFilterBlock(v_input, '$TEST_INPUT', spec=typespec, names=names, lang='php')

    if is_valid:
        s.also(stmt)
    else:
        with s.withTryBlock() as tryblock:
            tryblock.also(stmt)
            tryblock.alsoRaise(
                'Exception',
                msg='Invalid $TEST_INPUT should have raised exception',
            )
            with tryblock.withCatchBlock('UnexpectedValueException') as catchblock:
                catchblock.also(phpexpr('echo "all good";'))

    with TemporaryDirectory() as tmpdir:
        s.write_to_path(Path(tmpdir) / 'filter.php', lang="php")
        run(['php', 'filter.php'], cwd=tmpdir, check=True)
