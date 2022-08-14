from dataclasses import dataclass
from typing import List, Optional, Union

from . import Scenario


@dataclass
class Lever:
    label: str


@dataclass
class Toggle:
    label: str


@dataclass
class Button:
    label: str


@dataclass
class Gadget:
    name: str
    powerActivator: Optional[Union[Toggle, Button]]
    controls: List[Union[Lever, Toggle, Button]]


@dataclass
class Gizmo:
    name: str
    affordances: Union[List[Lever], List[Toggle], List[Button]]


GADGET0 = Scenario(
    [Gadget, Button, Toggle, Lever],
    {
        "__dataclass__": "Gadget",
        "name": "Digitizer 2000",
        "powerActivator": None,
        "controls": [
            {"__dataclass__": "Lever", "label": "Input Source"},
            {"__dataclass__": "Toggle", "label": "Compression"},
            {"__dataclass__": "Button", "label": "Eject"},
        ],
    },
    verify_php='''
        assert($VAR->name === "Digitizer 2000");
        assert($VAR->powerActivator === null);
        assert(is_array($VAR->controls));
        assert(count($VAR->controls) === 3);
        assert($VAR->controls[0] instanceof Lever);
        assert($VAR->controls[0]->label === "Input Source");
        assert($VAR->controls[1] instanceof Toggle);
        assert($VAR->controls[1]->label === "Compression");
    ''',
)


GADGET1 = Scenario(
    [Gadget, Button, Toggle, Lever],
    {
        "__dataclass__": "Gadget",
        "name": "Ultimate Power Box",
        "powerActivator": {"__dataclass__": "Toggle", "label": "POWER!"},
        "controls": [],
    },
    verify_php='''
        assert($VAR->name === "Ultimate Power Box");
        assert($VAR->powerActivator instanceof Toggle);
        assert($VAR->powerActivator->label === "POWER!");
        assert(is_array($VAR->controls));
        assert(count($VAR->controls) === 0);
    ''',
)


GIZMO0 = Scenario(
    [Gizmo, Button, Toggle, Lever],
    {
        "__dataclass__": "Gizmo",
        "name": "Colour Doohicky",
        "affordances": [
            {"__dataclass__": "Toggle", "label": "Red"},
            {"__dataclass__": "Toggle", "label": "Blue"},
        ],
    },
    verify_php='''
        assert($VAR->name === "Colour Doohicky");
        assert(is_array($VAR->affordances));
        assert(count($VAR->affordances) === 2);
        assert($VAR->affordances[0] instanceof Toggle);
        assert($VAR->affordances[0]->label === "Red");
        assert($VAR->affordances[1] instanceof Toggle);
        assert($VAR->affordances[1]->label === "Blue");
    ''',
)
