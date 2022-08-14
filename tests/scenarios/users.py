from dataclasses import dataclass
from typing import Dict, List

from . import Scenario


@dataclass
class User:
    userId: int
    userName: str
    colours: List[str]
    prefs: Dict[str, str]


USER0 = Scenario(
    [User],
    {
        "__dataclass__": "User",
        "userId": 55,
        "userName": "Fred",
        "colours": [],
        "prefs": {},
    },
    verify_php='''
        assert($VAR->userId === 55);
        assert($VAR->userName === "Fred");
        assert(is_array($VAR->colours));
        assert(count($VAR->colours) === 0);
        assert(is_array($VAR->prefs));
        assert(count($VAR->prefs) === 0);
    ''',
)


USER1 = Scenario(
    [User],
    {
        "__dataclass__": "User",
        "userId": 66,
        "userName": "Nigel",
        "colours": ["red", "blue"],
        "prefs": {"option1": "value1", "option2": "value2"},
    },
    verify_php='''
        assert($VAR->userId === 66);
        assert($VAR->userName === "Nigel");
        assert(is_array($VAR->colours));
        assert(count($VAR->colours) === 2);
        assert($VAR->colours[0] === 'red');
        assert($VAR->colours[1] === 'blue');
        assert(is_array($VAR->prefs));
        assert(count($VAR->prefs) === 2);
        assert($VAR->prefs['option1'] === 'value1');
        assert($VAR->prefs['option2'] === 'value2');
    ''',
)
