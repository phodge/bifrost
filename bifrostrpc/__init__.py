import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple

from typing_extensions import Literal

from bifrostrpc.typing import Advanced, FuncSpec, Type
from paradox.generate.files import FilePython, FileTS

if TYPE_CHECKING:
    import flask

Flavour = Literal['requests', 'abstract']

log = logging.getLogger()


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

    def get_flask_blueprint(self, name: str, import_name: str) -> "flask.Blueprint":
        from flask import Blueprint, Response

        bp = Blueprint(name, import_name)

        def _call(method: str) -> Response:
            from flask import make_response, request
            import json

            # FIXME: provide a reuseable way to attach authentication/security
            try:
                fn, spec = self.getThings(method)

                # GET request is allowed for methods with no arguments
                if request.method == 'GET':
                    # FIXME: apparently GET (and HEAD) are mandatory methods and must not return a
                    # 405 error code like we're doing here.
                    return make_response('Bifrost RPC method calls must be submitted by POST', 405)

                provided = request.get_json()

                # pop off the __showdataclass__ flag if it's present
                showdataclasses = bool(provided.pop("__showdataclass__", False))

                errors: List[str] = []
                # import the data - this will type-check the whole thing and turn dicts into
                # dataclasses as necessary, etc
                kwargs = spec.importArgs(provided, 'body', errors)
                if len(errors):
                    return make_response('.\n'.join(errors) + '.', 400)

                # now call the function
                try:
                    result: Any = fn(**kwargs)
                except ArgumentError as e:
                    errors = [e.args[0]]
                else:
                    # sanity-check the return value and convert fancy types (dataclasses) to plain
                    # dicts
                    errors = []
                    jsonSafe = spec.exportRetval(result, '<retval>', showdataclasses, errors)

                if len(errors):
                    # TODO: in production mode we  need to log errors rather than sending them to
                    # the client
                    return make_response('.\n'.join(errors) + '.', 500)

                # pack it up and send it back
                # TODO: don't do pretty output in production mode
                packed = json.dumps(jsonSafe, indent=2, sort_keys=True)
                response = make_response(packed, 200)
                response.headers['Content-Type'] = 'application/json'
                return response
            except InvalidMethodError:
                return make_response(f'invalid method name {method!r}', 501)
            except Exception as e:
                # FIXME: in production mode we  need to log errors rather than sending them to the
                # client
                log.exception(f'BifrostRPC {name!r}: Exception encountered')
                return make_response(str(e), 500)

        bp.route('/api.v1/call/<method>', methods=['GET', 'POST'])(_call)

        # FIXME: auto-generate a / route that lists the method calls and what they do

        return bp
