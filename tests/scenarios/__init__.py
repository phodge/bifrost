from typing import Any, Dict, List, Protocol, Type, Union

from paradox.expressions import PanExpr, Pannable, PanVar, pan
from paradox.generate.statements import HardCodedStatement
from paradox.interfaces import AcceptsStatements


def json_obj_to_php(obj: Any) -> str:
    if isinstance(obj, list):
        converted = (json_obj_to_php(item) for item in obj)
        return '[' + ', '.join(converted) + ']'

    if isinstance(obj, dict):
        converted = (
            json_obj_to_php(key) + ' => ' + json_obj_to_php(val)
            for key, val in obj.items()
        )
        return '[' + ', '.join(converted) + ']'

    if isinstance(obj, str):
        return '"' + obj.replace('\\', '\\\\').replace('"', '\\"') + '"'

    if isinstance(obj, int):
        return str(obj)

    if obj is True:
        return 'true'

    if obj is False:
        return 'false'

    assert obj is None
    return 'null'


def json_obj_to_python(obj: Any) -> str:
    return repr(obj)


class Scenario(Protocol):
    obj: Dict[str, Any]
    dataclasses: List[Type[Any]]

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        pass


def assert_eq(context: AcceptsStatements, expr1: PanExpr, expr2: Union[PanExpr, Pannable]) -> None:
    if not isinstance(expr2, PanExpr):
        expr2 = pan(expr2)
    context.also(HardCodedStatement(
        python=f'assert ({expr1.getPyExpr()[0]}) == ({expr2.getPyExpr()[0]})',
        php=f'assert(({expr1.getPHPExpr()[0]}) === ({expr2.getPHPExpr()[0]}));',
    ))


def assert_islist(context: AcceptsStatements, expr: PanExpr, *, size: int) -> None:
    context.also(HardCodedStatement(
        python=f'assert isinstance({expr.getPyExpr()[0]}, list)',
        php=f'assert(is_array({expr.getPHPExpr()[0]}));',
    ))
    context.also(HardCodedStatement(
        python=f'assert len({expr.getPyExpr()[0]}) == {size}',
        php=f'assert(count({expr.getPHPExpr()[0]}) === {size});',
    ))


def assert_isdict(context: AcceptsStatements, expr: PanExpr, *, size: int) -> None:
    context.also(HardCodedStatement(
        python=f'assert isinstance({expr.getPyExpr()[0]}, dict)',
        php=f'assert(is_array({expr.getPHPExpr()[0]}));',
    ))
    context.also(HardCodedStatement(
        python=f'assert len({expr.getPyExpr()[0]}) == {size}',
        php=f'assert(count({expr.getPHPExpr()[0]}) === {size});',
    ))


def assert_isinstance(context: AcceptsStatements, expr: PanExpr, what: str) -> None:
    context.also(HardCodedStatement(
        python=f'assert isinstance({expr.getPyExpr()[0]}, {what})',
        php=f'assert({expr.getPHPExpr()[0]} instanceof {what});',
    ))


def assert_true(context: AcceptsStatements, expr: PanExpr) -> None:
    context.also(HardCodedStatement(
        python=f'assert {expr.getPyExpr()[0]}',
        php=f'assert({expr.getPHPExpr()[0]});',
    ))


def assert_contains_text(context: AcceptsStatements, haystack: PanExpr, needle: str) -> None:
    haystackphp = haystack.getPHPExpr()[0]
    needlephp = pan(needle).getPHPExpr()[0]
    context.alsoImportPy('re')
    context.also(HardCodedStatement(
        python=f'assert re.search(r{needle!r}, {haystack.getPyExpr()[0]})',
        php=f'assert(strpos({haystackphp}, {needlephp}) !== false);',
    ))
