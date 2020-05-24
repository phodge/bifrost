from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from typing_extensions import Literal

from bifrostrpc.typing import Advanced, FuncSpec, Type
from paradox.generate.files import FilePython, FileTS

Flavour = Literal['requests', 'abstract']


class ArgumentError(Exception):
    """
    This can be raised inside your methods to send an error message back to the client.

    This is useful for telling a client when it is e.g. sending invalid argument values.
    """


class InvalidMethodError(Exception):
    pass


class BifrostRPCService:
    _targets: Dict[str, Callable[..., Any]]

    def __init__(self, targets: List[Callable[..., Any]]):
        self._targets = {fn.__name__: fn for fn in targets}
        self._adv: Advanced = Advanced()
        self._spec: Dict[str, FuncSpec] = {}

        # TODO: when we're dealing with a NewType in typescript, we have the choice of using the
        # matching primitive type (string/int/bool) or generating a type alias in typescript

        # TODO: when dataclasses are used, we have a choice between
        # A) creating a matching interface in typescript; or
        # B) creating a matching class in typescript
        #
        # The nice thing about (A) is that typescript programmer can have his own set of classes
        # that match the interface (maybe even one class that matches multiple interfaces?)

    def getThings(self, name: str) -> Tuple[Callable[..., Any], FuncSpec]:
        try:
            fn = self._targets[name]
        except KeyError:
            raise InvalidMethodError()

        return fn, self._getTypeSpec(name)

    def addNewType(self, newType: Type[Any]) -> None:
        self._adv.addNewType(newType)

    def addExternalType(self, newType: Type[Any], *, tsmodule: str = None) -> None:
        self._adv.addExternalType(newType, tsmodule=tsmodule)

    def addContextType(self, newType: Type[Any]) -> None:
        self._adv.addContextType(newType)

    def addDataclass(self, class_: Type[Any]) -> None:
        self._adv.addDataclass(class_)

    def _getTypeSpec(self, name: str) -> FuncSpec:
        try:
            return self._spec[name]
        except KeyError:
            pass

        try:
            fn = self._targets[name]
        except KeyError:
            raise InvalidMethodError()

        spec = FuncSpec(fn, self._adv)
        self._spec[name] = spec
        return spec

    def generateTypescriptWebClient(
        self,
        modulepath: Path,
        classname: str,
        *,
        npmroot: Path,
    ) -> None:
        from bifrostrpc.generators.typescript import generateClient

        generateClient(
            FileTS(modulepath, npmroot=npmroot),
            classname=classname,
            funcspecs=[(k, self._getTypeSpec(k)) for k in self._targets],
            adv=self._adv,
        )

    def generatePythonClient(
        self,
        modulepath: Path,
        classname: str,
        flavour: Flavour,
    ) -> None:
        from bifrostrpc.generators.python import generateClient

        generateClient(
            FilePython(modulepath),
            classname=classname,
            funcspecs=[(k, self._getTypeSpec(k)) for k in self._targets],
            adv=self._adv,
            flavour=flavour,
        )
