from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from paradox.expressions import PanIndexAccess, PanKeyAccess, PanVar
    from paradox.typing import CrossType


class Names:
    def __init__(self) -> None:
        self._names: Dict[str, bool] = {}

    def getSpecificName(
        self,
        name: str,
        assignable: bool,
        crosstype: "CrossType",
    ) -> "PanVar":
        from paradox.expressions import PanVar

        assert name not in self._names
        self._names[name] = assignable
        return PanVar(name, crosstype)

    def getNewName(
        self,
        origin: "Union[PanVar, PanIndexAccess, PanKeyAccess, str]",
        base: str,
        assignable: bool,
    ) -> str:
        from paradox.expressions import PanVar

        if isinstance(origin, PanVar):
            origin = origin.rawname
        else:
            assert isinstance(origin, str)

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

    def isAssignable(self, name: str) -> bool:
        return self._names[name]
