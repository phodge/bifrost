from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import Any, List, Literal, Optional, Union

import pytest
from paradox.expressions import PanVar
from paradox.generate.statements import HardCodedStatement
from paradox.output import Script
from paradox.typing import CrossAny

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
