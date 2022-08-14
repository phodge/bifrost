from typing import Any, Dict, List, Type


def json_obj_to_php(obj: Any) -> str:
    if isinstance(obj, list):
        converted = (json_obj_to_php(item) for item in obj)
        return '[' + ', '.join(converted) + ']'

    if isinstance(obj, dict):
        converted = (
            json_obj_to_php(key) + ' => ' + json_obj_to_php(val)
            for key, val in obj.items()
        )
        return '[' + ', '.join(converted) + ']'

    if isinstance(obj, str):
        return '"' + obj.replace('\\', '\\\\').replace('"', '\\"') + '"'

    if isinstance(obj, int):
        return str(obj)

    if obj is True:
        return 'true'

    if obj is False:
        return 'false'

    assert obj is None
    return 'null'


def json_obj_to_python(obj: Any) -> str:
    return repr(obj)


class Scenario:
    def __init__(
        self,
        dataclasses: List[Type[Any]],
        obj: Dict[str, Any],
        *,
        verify_php: str = None,
    ) -> None:
        self.dataclasses: List[Type[Any]] = dataclasses
        self.obj = obj
        self._verify_php = verify_php

    @property
    def verify_php(self) -> str:
        if not self._verify_php:
            raise Exception("Not set")
        return self._verify_php

