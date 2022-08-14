from dataclasses import dataclass
from typing import Optional, Union

from typing_extensions import Literal

from . import Scenario


@dataclass
class Pet:
    name: str
    species: Union[Literal['dog'], Literal['cat']]
    age: Optional[int]


PET0 = Scenario(
    [Pet],
    {
        "__dataclass__": "Pet",
        "name": "Billy",
        "species": "dog",
        "age": 8,
    },
    verify_php='''
        assert($VAR->name === "Billy");
        assert($VAR->species === "dog");
        assert($VAR->age === 8);
    ''',
)


PET1 = Scenario(
    [Pet],
    {
        "__dataclass__": "Pet",
        "name": "Basil",
        "species": "cat",
    },
    verify_php='''
        assert($VAR->name === "Basil");
        assert($VAR->species === "cat");
        assert($VAR->age === null);
    ''',
)
