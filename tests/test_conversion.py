from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any, List, Optional, Union

import pytest
from paradox.expressions import PanVar, phpexpr
from paradox.generate.files import FilePHP
from paradox.typing import CrossAny

from .scenarios import Scenario, json_obj_to_php
from .scenarios.gadgets import (DEVICE0, DEVICE1, GADGET0, GADGET1, GIZMO0,
                                WIDGET0, WIDGET1)
from .scenarios.pets import PET0, PET1
from .scenarios.travellers import TRAVELLER0, TRAVELLER1
from .scenarios.users import USER0, USER1


def _run_php(script: str, **kwargs: Any) -> None:
    cmd = ['php', '-d', 'assert.exception=1', script]
    run(cmd, **kwargs)


@pytest.mark.parametrize('scenario', [
    USER0,
    USER1,
    PET0,
    PET1,
    TRAVELLER0,
    TRAVELLER1,
    GADGET0,
    GADGET1,
    GIZMO0,
    WIDGET0,
    WIDGET1,
    DEVICE0,
    DEVICE1,
])
def test_get_dataclass_spec_php(scenario: Scenario) -> None:
    from bifrostrpc.generators.conversion import getDataclassSpec
    from bifrostrpc.typing import Advanced

    # load dataclasses
    adv = Advanced()
    for dc in scenario.dataclasses:
        adv.addDataclass(dc)

    classname = scenario.dataclasses[0].__name__
    phpinit = f'''
        $VAR = {classname}::fromDict(
            {json_obj_to_php(scenario.obj)},
            "\\$_"
        )
        '''

    with TemporaryDirectory() as tmpdir:
        f = FilePHP(Path(tmpdir) / 'dataclass.php')
        for dc in scenario.dataclasses:
            f.contents.also(getDataclassSpec(dc, adv=adv, lang='php'))
        f.contents.also(phpexpr(dedent(phpinit)))
        f.contents.also(phpexpr(f'assert($VAR instanceof {classname})'))
        f.contents.also(phpexpr(dedent(scenario.verify_php)))
        f.writefile()
        _run_php('dataclass.php', cwd=tmpdir, check=True)


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
