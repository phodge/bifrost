from dataclasses import dataclass
from typing import Literal, Optional, Union

from paradox.expressions import PanVar
from paradox.interfaces import AcceptsStatements

from . import Scenario, assert_eq


@dataclass
class Pet:
    name: str
    species: Union[Literal['dog'], Literal['cat']]
    age: Optional[int]


class PET0(Scenario):
    dataclasses = [Pet]
    obj = {
        "__dataclass__": "Pet",
        "name": "Billy",
        "species": "dog",
        "age": 8,
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Billy")
        assert_eq(context, v.getprop('species'), "dog")
        assert_eq(context, v.getprop('age'), 8)


class PET1(Scenario):
    dataclasses = [Pet]
    obj = {
        "__dataclass__": "Pet",
        "name": "Basil",
        "species": "cat",
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Basil")
        assert_eq(context, v.getprop('species'), "cat")
        assert_eq(context, v.getprop('age'), None)
