from dataclasses import dataclass
from typing import Dict, List, Optional, Union

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


@dataclass
class Widget:
    name: str
    inputs: Union[List[Toggle], List[Button], List[int]]


@dataclass
class Device:
    name: str
    interfaces: Dict[str, Button]
    settings: Optional[Dict[str, Union[Button, Toggle]]]


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


WIDGET0 = Scenario(
    [Widget, Toggle, Button],
    {
        "__dataclass__": "Widget",
        "name": "Uberwidget",
        "inputs": [
            {"__dataclass__": "Toggle", "label": "Red"},
            {"__dataclass__": "Toggle", "label": "Blue"},
            {"__dataclass__": "Toggle", "label": "Green"},
        ],
    },
    verify_php='''
        assert($VAR->name === "Uberwidget");
        assert(is_array($VAR->inputs));
        assert(count($VAR->inputs) === 3);
        assert($VAR->inputs[0] instanceof Toggle);
        assert($VAR->inputs[1] instanceof Toggle);
        assert($VAR->inputs[2] instanceof Toggle);
        assert($VAR->inputs[0]->label === "Red");
        assert($VAR->inputs[1]->label === "Blue");
        assert($VAR->inputs[2]->label === "Green");
    ''',
)


WIDGET1 = Scenario(
    [Widget, Toggle, Button],
    {
        "__dataclass__": "Widget",
        "name": "Uberwidget",
        "inputs": [55, 66, 77, 99],
    },
    verify_php='''
        assert($VAR->name === "Uberwidget");
        assert(is_array($VAR->inputs));
        assert(count($VAR->inputs) === 4);
        assert(is_int($VAR->inputs[0]));
        assert(is_int($VAR->inputs[1]));
        assert(is_int($VAR->inputs[2]));
        assert(is_int($VAR->inputs[3]));
        assert($VAR->inputs[0] === 55);
        assert($VAR->inputs[1] === 66);
        assert($VAR->inputs[2] === 77);
        assert($VAR->inputs[3] === 99);
    ''',
)


DEVICE0 = Scenario(
    [Device, Button, Toggle],
    {
        "__dataclass__": "Device",
        "name": "Device Zero",
        "interfaces": [
            {"__dataclass__": "Button", "label": "On"},
            {"__dataclass__": "Button", "label": "Off"},
        ],
        "settings": {
            "dehumidifier": {"__dataclass__": "Button", "label": "Active"},
            "auto-adjust": {"__dataclass__": "Toggle", "label": "Auto"},
        },
    },
    verify_php='''
        assert($VAR->name === "Device Zero");
        assert(is_array($VAR->interfaces));
        assert(count($VAR->interfaces) === 2);
        assert($VAR->interfaces[0] instanceof Button);
        assert($VAR->interfaces[1] instanceof Button);
        assert($VAR->interfaces[0]->label === "On");
        assert($VAR->interfaces[1]->label === "Off");
        assert(is_array($VAR->settings));
        assert(count($VAR->settings) === 2);
        assert($VAR->settings["dehumidifier"] instanceof Button);
        assert($VAR->settings["auto-adjust"]  instanceof Toggle);
        assert($VAR->settings["dehumidifier"]->label === "Active");
        assert($VAR->settings["auto-adjust"]->label === "Auto");
    ''',
)


DEVICE1 = Scenario(
    [Device, Button, Toggle],
    {
        "__dataclass__": "Device",
        "name": "The One Device",
        "interfaces": {},
        "settings": {},
    },
    verify_php='''
        assert($VAR->name === "The One Device");
        assert(is_array($VAR->interfaces));
        assert(count($VAR->interfaces) === 0);
        assert(is_array($VAR->settings));
        assert(count($VAR->settings) === 0);
    ''',
)


DEVICE2 = Scenario(
    [Device, Button, Toggle],
    {
        "__dataclass__": "Device",
        "name": "Device, Too",
        "interfaces": {},
        # NOTE: this is where we demonstrate that an Optional dataclass property can be safely
        # omitted
    },
    verify_php='''
        assert($VAR->name === "Device, Too");
        assert(is_array($VAR->interfaces));
        assert(count($VAR->interfaces) === 0);
        assert($VAR->settings === null);
    ''',
)
