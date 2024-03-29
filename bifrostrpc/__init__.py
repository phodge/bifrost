import logging
from pathlib import Path
from typing import (TYPE_CHECKING, Any, Callable, Dict, List, Literal,
                    Optional, Tuple, Type, TypeVar)

from paradox.output import Script

from bifrostrpc.typing import Advanced  # pylint: disable=cyclic-import
from bifrostrpc.typing import FuncSpec

if TYPE_CHECKING:
    import flask

Flavour = Literal['requests', 'abstract']

log = logging.getLogger()

T = TypeVar('T')


class ArgumentError(Exception):
    """
    This can be raised inside your methods to send an error message back to the client.

    This is useful for telling a client when it is e.g. sending invalid argument values.
    """


class InvalidMethodError(Exception):
    pass


class TypeNotSupportedError(Exception):
    """Raised when you try to add a method with a type which can't be supported.

    E.g. there is no clear way to support "typing.Any" over network calls, so it's not supported.
    """


class AuthFailure(Exception):
    """Raised inside an Auth Type factory to send a specific message back to the client."""


class BifrostRPCService:
    _targets: Dict[str, Callable[..., Any]]

    def __init__(self, targets: List[Callable[..., Any]] = None):
        self._targets = {fn.__name__: fn for fn in (targets or [])}
        self._adv: Advanced = Advanced()
        self._spec: Dict[str, FuncSpec] = {}
        self._factory: Dict[Type[Any], Callable[[], Any]] = {}

        # TODO: when we're dealing with a NewType in typescript, we have the choice of using the
        # matching primitive type (string/int/bool) or generating a type alias in typescript

        # TODO: when dataclasses are used, we have a choice between
        # A) creating a matching interface in typescript; or
        # B) creating a matching class in typescript
        #
        # The nice thing about (A) is that typescript programmer can have his own set of classes
        # that match the interface (maybe even one class that matches multiple interfaces?)

    def rpcmethod(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        name = fn.__name__
        if name in self._targets:
            raise Exception(f"A target named {name} already exists")
        self._targets[name] = fn
        return fn

    def getThings(self, name: str) -> Tuple[Callable[..., Any], FuncSpec]:
        try:
            fn = self._targets[name]
        except KeyError:
            raise InvalidMethodError()

        return fn, self._getTypeSpec(name)

    def addNewType(self, newType: Type[Any]) -> None:
        self._adv.addNewType(newType)

    def addExternalType(self, newType: Type[Any], *, tsmodule: str) -> None:
        self._adv.addExternalType(newType, tsmodule=tsmodule)

    def addInternalType(
        self,
        newType: Type[T],
        factory: Callable[[], T],
    ) -> None:
        assert newType not in self._factory
        self._adv.addContextType(newType)
        self._factory[newType] = factory

    def addAuthType(
        self,
        newType: Type[T],
        factory: Callable[[], Optional[T]],
    ) -> None:
        assert newType not in self._factory
        self._adv.addAuthType(newType)
        self._factory[newType] = factory

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
        npmroot: Path,  # pylint: disable=unused-argument
        flavour: Literal['abstract'],
    ) -> None:
        # pylint: disable=cyclic-import
        from bifrostrpc.generators.typescript import generateClient

        script = Script()

        generateClient(
            script,
            classname=classname,
            funcspecs=[(k, self._getTypeSpec(k)) for k in self._targets],
            adv=self._adv,
            flavour=flavour,
        )

        # TODO: turn pretty on when paradox adds support
        # NOTE: we expect this is what the `npmroot` arg will be needed for
        script.write_to_path(modulepath, lang='typescript', pretty=False)

    def generatePythonClient(
        self,
        modulepath: Path,
        classname: str,
        flavour: Flavour,
    ) -> None:
        # pylint: disable=cyclic-import
        from bifrostrpc.generators.python import generateClient

        script = Script()

        generateClient(
            script,
            classname=classname,
            funcspecs=[(k, self._getTypeSpec(k)) for k in self._targets],
            adv=self._adv,
            flavour=flavour,
        )

        # TODO: turn pretty on when paradox adds support
        script.write_to_path(modulepath, lang='python', pretty=False)

    def generatePHPClient(
        self,
        filepath: Path,
        classname: str,
        flavour: Literal['abstract'],
        on_error: Literal['return', 'raise'] = 'return',
    ) -> None:
        # pylint: disable=cyclic-import
        from bifrostrpc.generators.php import generateClient

        script = Script()

        generateClient(
            script,
            classname=classname,
            funcspecs=[(k, self._getTypeSpec(k)) for k in self._targets],
            adv=self._adv,
            flavour=flavour,
            on_error=on_error,
        )

        # TODO: turn pretty on when paradox adds support
        script.write_to_path(filepath, lang='php', pretty=False)

    def get_flask_blueprint(self, name: str, import_name: str) -> "flask.Blueprint":
        from flask import Blueprint, Response

        bp = Blueprint(name, import_name)

        def _call(method: str) -> Response:
            import json

            from flask import make_response, request

            # FIXME: provide a reuseable way to attach authentication/security
            try:
                fn, spec = self.getThings(method)

                # TODO: we should be rethinking errors / error codes and make sure the generated
                # clients handle these scenarios correctly and visibly.
                # - server error (503 etc)
                # - network outage
                # - client error (e.g. sending a HTTP GET instead of POST)
                # - client misuse (passing wrong data type to a generated client method)
                # Also this might be the point where we rethink whether it was a good idea to
                # return error codes as values instead of raising them as exceptions.

                # GET request is allowed for methods with no arguments
                if request.method == 'GET':
                    # FIXME: apparently GET (and HEAD) are mandatory methods and must not return a
                    # 405 error code like we're doing here.
                    return make_response('Bifrost RPC method calls must be submitted by POST', 405)

                provided = request.get_json()
                if not isinstance(provided, dict):
                    return make_response('Request body must be a JSON object', 400)

                # pop off the __showdataclass__ flag if it's present
                showdataclasses = bool(provided.pop("__showdataclass__", False))

                errors: List[str] = []
                # import the data - this will type-check the whole thing and turn dicts into
                # dataclasses as necessary, etc
                kwargs = spec.importArgs(provided, 'body', lambda err: errors.append(err))
                if errors:
                    return make_response('.\n'.join(errors) + '.', 400)

                authorized = False
                for name, t in spec.authvars.items():
                    factory = self._factory[t]
                    try:
                        value = factory()
                    except AuthFailure as e:
                        return make_response(e.args[0], 401)

                    if not value:
                        log.info(
                            f"{method}(): Authorization error"
                            f": factory for {name}: {t.__name__} returned a Falsy value."
                        )
                        return make_response('Unknown authorization error', 401)

                    kwargs[name] = value
                    authorized = True

                if not authorized:
                    log.error(
                        f"{method}(): Authorization error"
                        f": No auth vars configured for this method."
                    )
                    return make_response('Authorization error', 401)

                # set up context for the function call
                for name, t in spec.contextvars.items():
                    factory = self._factory[t]
                    kwargs[name] = factory()

                # now call the function
                try:
                    result: Any = fn(**kwargs)
                except ArgumentError as e:
                    errors = [e.args[0]]
                else:
                    def handle_err(msg: str) -> None:
                        # TODO: raise a more specific exception type here
                        raise Exception(f"method response was invalid: {msg}")

                    # sanity-check the return value and convert fancy types (dataclasses) to plain
                    # dicts
                    errors = []
                    jsonSafe = spec.exportRetval(
                        result,
                        '<retval>',
                        showdataclasses,
                        onerr=handle_err,
                    )

                if errors:
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
            except Exception as e:  # pylint: disable=broad-except
                # FIXME: in production mode we  need to log errors rather than sending them to the
                # client
                log.exception(f'BifrostRPC {name!r}: Exception encountered')
                return make_response(str(e), 500)

        bp.route('/api.v1/call/<method>', methods=['GET', 'POST'])(_call)

        # FIXME: auto-generate a / route that lists the method calls and what they do

        return bp
