from dataclasses import dataclass
from typing import Dict, List

from paradox.expressions import PanVar
from paradox.interfaces import AcceptsStatements
from paradox.typing import CrossAny

from . import Scenario, assert_eq, assert_isdict, assert_islist


@dataclass
class User:
    userId: int
    userName: str
    colours: List[str]
    prefs: Dict[str, str]


class USER0(Scenario):
    dataclasses = [User]
    obj = {
        "__dataclass__": "User",
        "userId": 55,
        "userName": "Fred",
        "colours": [],
        "prefs": {},
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('userId', CrossAny()), 55)
        assert_eq(context, v.getprop('userName', CrossAny()), "Fred")

        assert_islist(context, v.getprop('colours', CrossAny()), size=0)
        assert_isdict(context, v.getprop('prefs', CrossAny()), size=0)


class USER1(Scenario):
    dataclasses = [User]
    obj = {
        "__dataclass__": "User",
        "userId": 66,
        "userName": "Nigel",
        "colours": ["red", "blue"],
        "prefs": {"option1": "value1", "option2": "value2"},
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('userId', CrossAny()), 66)
        assert_eq(context, v.getprop('userName', CrossAny()), 'Nigel')
        p_colours = v.getprop('colours', CrossAny())
        assert_islist(context, p_colours, size=2)
        assert_eq(context, p_colours.getindex(0), 'red')
        assert_eq(context, p_colours.getindex(1), 'blue')

        p_prefs = v.getprop('prefs', CrossAny())
        assert_isdict(context, p_prefs, size=2)
        assert_eq(context, p_prefs.getitem('option1'), 'value1')
        assert_eq(context, p_prefs.getitem('option2'), 'value2')
