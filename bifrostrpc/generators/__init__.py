from typing import Dict, Union

from paradox.expressions import PanVar
from paradox.typing import CrossType

# Prevent warnings about args named 'type'
# pylint: disable=W0622


class Names:
    def __init__(self) -> None:
        self._names: Dict[str, bool] = {}

    def getSpecificName(
        self,
        name: str,
        assignable: bool,
        type: CrossType = None,
    ) -> PanVar:
        assert name not in self._names
        self._names[name] = assignable
        return PanVar(name, type)

    # TODO: replace all use of old getNewName() with getNewName2() then
    # back-replace name
    def getNewName2(
        self,
        origin: str,
        base: str,
        assignable: bool,
        *,
        type: CrossType = None,
    ) -> PanVar:
        return PanVar(self.getNewName(origin, base, assignable), type)

    def getNewName(
        self,
        origin: str,
        base: str,
        assignable: bool,
    ) -> str:
        # if there is a dot in the name, grab everything after
        if '.' in origin:
            origin = origin.split('.')[-1]

        # replace out '[' and ']' characters
        origin = origin.replace('[', '')
        origin = origin.replace(']', '')

        attempt = origin + '_' + base
        suffix = 0
        while attempt in self._names:
            suffix += 1
            if suffix > 100:
                raise Exception("couldn't get a unique name")
            attempt = origin + '_' + base + str(suffix)
        self._names[attempt] = assignable
        return attempt

    def isAssignable(self, name: Union[str, PanVar]) -> bool:
        if isinstance(name, PanVar):
            return self._names[name.rawname]

        return self._names[name]
