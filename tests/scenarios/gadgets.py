from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from paradox.expressions import PanVar, isint
from paradox.interfaces import AcceptsStatements
from paradox.typing import CrossAny

from . import (Scenario, assert_eq, assert_isdict, assert_isinstance,
               assert_islist, assert_true)


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


@dataclass
class Machine:
    name: str
    subunits: List[Dict[str, Union[Gadget, Gizmo]]]


class GADGET0(Scenario):
    dataclasses = [Gadget, Button, Toggle, Lever]
    obj = {
        "__dataclass__": "Gadget",
        "name": "Digitizer 2000",
        "powerActivator": None,
        "controls": [
            {"__dataclass__": "Lever", "label": "Input Source"},
            {"__dataclass__": "Toggle", "label": "Compression"},
            {"__dataclass__": "Button", "label": "Eject"},
        ],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name', CrossAny()), "Digitizer 2000")
        assert_eq(context, v.getprop('powerActivator', CrossAny()), None)

        p_controls = v.getprop('controls', CrossAny())
        assert_islist(context, p_controls, size=3)
        assert_isinstance(context, p_controls.getindex(0), 'Lever')
        assert_isinstance(context, p_controls.getindex(1), 'Toggle')
        assert_isinstance(context, p_controls.getindex(2), 'Button')
        assert_eq(context, p_controls.getindex(0).getprop('label', CrossAny()), "Input Source")
        assert_eq(context, p_controls.getindex(1).getprop('label', CrossAny()), "Compression")
        assert_eq(context, p_controls.getindex(2).getprop('label', CrossAny()), "Eject")


class GADGET1(Scenario):
    dataclasses = [Gadget, Button, Toggle, Lever]
    obj = {
        "__dataclass__": "Gadget",
        "name": "Ultimate Power Box",
        "powerActivator": {"__dataclass__": "Toggle", "label": "POWER!"},
        "controls": [],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Ultimate Power Box")
        assert_isinstance(context, v.getprop('powerActivator'), 'Toggle')
        assert_eq(context, v.getprop('powerActivator').getprop('label'), "POWER!")
        assert_islist(context, v.getprop('controls'), size=0)


class GIZMO0(Scenario):
    dataclasses = [Gizmo, Button, Toggle, Lever]
    obj = {
        "__dataclass__": "Gizmo",
        "name": "Colour Doohicky",
        "affordances": [
            {"__dataclass__": "Toggle", "label": "Red"},
            {"__dataclass__": "Toggle", "label": "Blue"},
        ],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Colour Doohicky")
        assert_islist(context, v.getprop('affordances'), size=2)
        assert_isinstance(context, v.getprop("affordances").getindex(0), 'Toggle')
        assert_isinstance(context, v.getprop("affordances").getindex(1), 'Toggle')
        assert_eq(context, v.getprop('affordances').getindex(0).getprop('label'), "Red")
        assert_eq(context, v.getprop('affordances').getindex(1).getprop('label'), "Blue")


class WIDGET0(Scenario):
    dataclasses = [Widget, Toggle, Button]
    obj = {
        "__dataclass__": "Widget",
        "name": "Uberwidget",
        "inputs": [
            {"__dataclass__": "Toggle", "label": "Red"},
            {"__dataclass__": "Toggle", "label": "Blue"},
            {"__dataclass__": "Toggle", "label": "Green"},
        ],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Uberwidget")
        assert_islist(context, v.getprop('inputs'), size=3)
        assert_isinstance(context, v.getprop('inputs').getindex(0), 'Toggle')
        assert_isinstance(context, v.getprop('inputs').getindex(1), 'Toggle')
        assert_isinstance(context, v.getprop('inputs').getindex(2), 'Toggle')
        assert_eq(context, v.getprop('inputs').getindex(0).getprop('label'), "Red")
        assert_eq(context, v.getprop('inputs').getindex(1).getprop('label'), "Blue")
        assert_eq(context, v.getprop('inputs').getindex(2).getprop('label'), "Green")


class WIDGET1(Scenario):
    dataclasses = [Widget, Toggle, Button]
    obj = {
        "__dataclass__": "Widget",
        "name": "Uberwidget",
        "inputs": [55, 66, 77, 99],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Uberwidget")
        assert_islist(context, v.getprop('inputs'), size=4)
        assert_true(context, isint(v.getprop('inputs').getindex(0)))
        assert_true(context, isint(v.getprop('inputs').getindex(1)))
        assert_true(context, isint(v.getprop('inputs').getindex(2)))
        assert_true(context, isint(v.getprop('inputs').getindex(3)))
        assert_eq(context, v.getprop('inputs').getindex(0), 55)
        assert_eq(context, v.getprop('inputs').getindex(1), 66)
        assert_eq(context, v.getprop('inputs').getindex(2), 77)
        assert_eq(context, v.getprop('inputs').getindex(3), 99)


class DEVICE0(Scenario):
    dataclasses = [Device, Button, Toggle]
    obj = {
        "__dataclass__": "Device",
        "name": "Device Zero",
        "interfaces": {
            'on': {"__dataclass__": "Button", "label": "On"},
            'off': {"__dataclass__": "Button", "label": "Off"},
        },
        "settings": {
            "dehumidifier": {"__dataclass__": "Button", "label": "Active"},
            "auto-adjust": {"__dataclass__": "Toggle", "label": "Auto"},
        },
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name', CrossAny()), "Device Zero")

        p_interfaces = v.getprop('interfaces', CrossAny())
        assert_isdict(context, p_interfaces, size=2)
        i_on = p_interfaces.getitem('on')
        i_off = p_interfaces.getitem('off')
        assert_isinstance(context, i_on, 'Button')
        assert_isinstance(context, i_off, 'Button')
        assert_eq(context, i_on.getprop('label', CrossAny()), 'On')
        assert_eq(context, i_off.getprop('label', CrossAny()), 'Off')

        p_settings = v.getprop('settings', CrossAny())
        assert_isdict(context, p_settings, size=2)
        i_dehumid = p_settings.getitem("dehumidifier")
        i_autoadj = p_settings.getitem("auto-adjust")
        assert_isinstance(context, i_dehumid, 'Button')
        assert_isinstance(context, i_autoadj, 'Toggle')
        assert_eq(context, i_dehumid.getprop('label', CrossAny()), 'Active')
        assert_eq(context, i_autoadj.getprop('label', CrossAny()), 'Auto')


class DEVICE1(Scenario):
    dataclasses = [Device, Button, Toggle]
    obj = {
        "__dataclass__": "Device",
        "name": "The One Device",
        "interfaces": {},
        "settings": {},
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name', CrossAny()), "The One Device")
        assert_isdict(context, v.getprop('interfaces', CrossAny()), size=0)
        assert_isdict(context, v.getprop('settings', CrossAny()), size=0)


class DEVICE2(Scenario):
    dataclasses = [Device, Button, Toggle]
    obj = {
        "__dataclass__": "Device",
        "name": "Device, Too",
        "interfaces": {},
        # NOTE: this is where we demonstrate that an Optional dataclass property can be safely
        # omitted
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name', CrossAny()), "Device, Too")
        assert_isdict(context, v.getprop('interfaces', CrossAny()), size=0)
        assert_eq(context, v.getprop('settings', CrossAny()), None)


class MACHINE0(Scenario):
    dataclasses = [Machine, Gadget, Gizmo, Toggle, Button, Lever]
    obj = {
        "__dataclass__": "Machine",
        "name": "Deus Ex Machina",
        "subunits": [
            {
                "G001": {
                    "__dataclass__": "Gadget",
                    "name": "G001",
                    "controls": [
                        {"__dataclass__": "Button", "label": "Alpha"},
                        {"__dataclass__": "Button", "label": "Beta"},
                    ],
                },
                "G002": {
                    "__dataclass__": "Gizmo",
                    "name": "G002",
                    "affordances": [
                        {"__dataclass__": "Toggle", "label": "Gamma"},
                        {"__dataclass__": "Toggle", "label": "Delta"},
                        {"__dataclass__": "Toggle", "label": "Epsilon"},
                    ],
                },
            },
            {
                "J003": {
                    "__dataclass__": "Gizmo",
                    "name": "J003",
                    "affordances": [],
                },
                "J004": {
                    "__dataclass__": "Gadget",
                    "name": "J004",
                    "controls": [
                        {"__dataclass__": "Lever", "label": "Zeta"},
                    ],
                    "powerActivator": {"__dataclass__": "Button", "label": "Eta"},
                },
            },
        ],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name', CrossAny()), "Deus Ex Machina")
        p_subunits = v.getprop('subunits', CrossAny())
        assert_islist(context, p_subunits, size=2)
        sub0 = p_subunits.getindex(0)
        sub1 = p_subunits.getindex(1)
        assert_isdict(context, sub0, size=2)
        assert_isdict(context, sub1, size=2)
        G001 = sub0.getitem("G001")
        G002 = sub0.getitem("G002")
        J003 = sub1.getitem("J003")
        J004 = sub1.getitem("J004")

        assert_isinstance(context, G001, 'Gadget')
        assert_eq(context, G001.getprop('name', CrossAny()), 'G001')
        G001_controls = G001.getprop('controls', CrossAny())
        assert_islist(context, G001_controls, size=2)
        assert_isinstance(context, G001_controls.getindex(0), 'Button')
        assert_isinstance(context, G001_controls.getindex(1), 'Button')
        assert_eq(context, G001_controls.getindex(0).getprop('label', CrossAny()), "Alpha")
        assert_eq(context, G001_controls.getindex(1).getprop('label', CrossAny()), "Beta")
        assert_eq(context, G001.getprop('powerActivator', CrossAny()), None)

        assert_isinstance(context, G002, 'Gizmo')
        assert_eq(context, G002.getprop('name'), "G002")
        assert_islist(context, G002.getprop('affordances'), size=3)
        assert_isinstance(context, G002.getprop('affordances').getindex(0), 'Toggle')
        assert_isinstance(context, G002.getprop('affordances').getindex(1), 'Toggle')
        assert_isinstance(context, G002.getprop('affordances').getindex(2), 'Toggle')
        assert_eq(context, G002.getprop('affordances').getindex(0).getprop('label'), "Gamma")
        assert_eq(context, G002.getprop('affordances').getindex(1).getprop('label'), "Delta")
        assert_eq(context, G002.getprop('affordances').getindex(2).getprop('label'), "Epsilon")

        assert_isinstance(context, J003, 'Gizmo')
        assert_eq(context, J003.getprop('name', CrossAny()), "J003")
        assert_islist(context, J003.getprop('affordances', CrossAny()), size=0)

        assert_isinstance(context, J004, 'Gadget')
        assert_eq(context, J004.getprop('name'), "J004")
        assert_islist(context, J004.getprop('controls'), size=1)
        c0 = J004.getprop('controls').getindex(0)
        assert_isinstance(context, c0, 'Lever')
        assert_eq(context, c0.getprop('label'), "Zeta")
        assert_isinstance(context, J004.getprop('powerActivator'), 'Button')
        assert_eq(context, J004.getprop('powerActivator').getprop('label'), "Eta")


class MACHINE1(Scenario):
    dataclasses = [Machine, Gadget, Gizmo, Toggle, Button, Lever]
    obj = {
        "__dataclass__": "Machine",
        "name": "Rage Against the Machine",
        "subunits": [{}, {}, {}, {}],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Rage Against the Machine")
        assert_islist(context, v.getprop('subunits'), size=4)
        assert_isdict(context, v.getprop('subunits').getindex(0), size=0)
        assert_isdict(context, v.getprop('subunits').getindex(1), size=0)
        assert_isdict(context, v.getprop('subunits').getindex(2), size=0)
        assert_isdict(context, v.getprop('subunits').getindex(3), size=0)


class MACHINE2(Scenario):
    dataclasses = [Machine, Gadget, Gizmo, Toggle, Button, Lever]
    obj = {
        "__dataclass__": "Machine",
        "name": "Null Machine",
        "subunits": [],
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('name'), "Null Machine")
        assert_islist(context, v.getprop('subunits'), size=0)
