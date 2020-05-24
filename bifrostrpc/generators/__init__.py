from typing import Dict


class Names:
    def __init__(self) -> None:
        self._names: Dict[str, bool] = {}

    def getNewName(self, origin: str, base: str, assignable: bool) -> str:
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
