from pathlib import Path
from typing import Union

from paradox.expressions import (PanAwait, PanCall, PanDict, PanExpr, PanProp,
                                 PanVar, pan)
from paradox.generate.statements import FunctionSpec, HardCodedStatement
from paradox.interfaces import AcceptsStatements
from paradox.output import Script
from paradox.typing import CrossAny, CrossCustomType, CrossStr, listof, unionof

from tests.conftest import DemoRunner
from tests.scenarios import (assert_contains_text, assert_eq,
                             assert_isinstance, assert_islist)

DEMO_SERVICE_ROOT = Path(__file__).parent / 'demo_service'


def _assert_exception_message(
    demo_runner: DemoRunner,
    s: AcceptsStatements,
    v_caught: PanVar,
    expectedmsg: str,
) -> None:
    msgexpr: PanExpr
    if demo_runner.lang in 'php':
        if demo_runner.errors == 'return':
            msgexpr = v_caught.getprop('message')
        else:
            msgexpr = PanCall(v_caught.getprop('getMessage'))
    elif demo_runner.lang == 'python':
        assert demo_runner.errors == 'return'
        msgexpr = v_caught.getprop('message')
    elif demo_runner.lang == 'typescript':
        # not currently used
        raise Exception("TODO: implement this")
        msgexpr = v_caught.getprop('message')
    else:
        raise Exception(f"Not implemented for {demo_runner.lang}")
    assert_contains_text(s, msgexpr, expectedmsg)


def _expect_error(
    demo_runner: DemoRunner,
    s: AcceptsStatements,
    expr: PanExpr,
    errclass: str,
    expectedmsg: str,
) -> None:
    if demo_runner.errors == 'raise':
        with s.withTryBlock() as tryblock:
            tryblock.also(expr)
            tryblock.alsoRaise(
                # TODO: 'Exception' is the wrong constructor for TypeScript/JS and won't work
                ctor='Exception',
                msg=f'ERROR: {errclass} was not thrown',
            )
            v_err = PanVar('e', type=CrossAny())
            with tryblock.withCatchBlock2(
                v_err,
                pyclass=errclass,
                phpclass=errclass,
                tsclass=errclass,
            ) as catchblock:
                _assert_exception_message(demo_runner, catchblock, v_err, expectedmsg)
    else:
        v_result = s.alsoDeclare('result', 'no_type', expr)
        assert_isinstance(s, v_result, errclass)
        _assert_exception_message(demo_runner, s, v_result, expectedmsg)


def test_generated_client(
    demo_runner: DemoRunner,
) -> None:
    s = Script()

    if demo_runner.lang == 'typescript':
        if demo_runner.flavour == 'fetch':
            # TODO: not yet implemented
            return

        # typescript requires await due to use of Promises
        def await_call(
            target: Union[str, PanProp],
            *args: PanExpr,
            **kwargs: PanExpr,
        ) -> PanExpr:
            return PanAwait(PanCall(target, *args, **kwargs))

        # NOTE: we need to wrap the assertions in an async function because CommonJS format
        # doesn't permit await at the top level
        ctx: AcceptsStatements = s.also(FunctionSpec('test_body', 'no_return', isasync=True))
    else:
        # no need for await syntax in other languages
        def await_call(
            target: Union[str, PanProp],
            *args: PanExpr,
            **kwargs: PanExpr,
        ) -> PanExpr:
            return PanCall(target, *args, **kwargs)

        ctx = s

    s.also(HardCodedStatement(
        php='require "get_client.php";',
        python=None,
        typescript=None,
    ))

    s.remark('load the client')
    s.alsoImportPy('get_client', ['get_client'])
    s.alsoImportTS('./get_client', ['get_client'])
    v_client = s.alsoDeclare('v_client', 'no_type', PanCall('get_client'))

    ctx.remark('simple string-reversal endpoint')
    assert_eq(
        ctx,
        await_call(v_client.getprop('get_reversed'), pan("Hello world")),
        "dlrow olleH",
    )

    t_Pet = CrossCustomType(
        python='Pet',
        phplang='Pet',
        phpdoc='Pet',
        typescript='Pet',
    )
    t_ApiFailure = CrossCustomType(
        python='ApiFailure',
        phplang='ApiFailure',
        phpdoc='ApiFailure',
        typescript='ApiFailure',
    )
    s.alsoImportPy('generated_client', ['Pet', 'ApiFailure'])
    s.alsoImportTS('./generated_client', ['Pet', 'ApiFailure'])

    ctx.remark('method with a more complex return type')
    v_pets = ctx.alsoDeclare(
        'pets',
        unionof(listof(t_Pet), t_ApiFailure),
        await_call(v_client.getprop('get_pets')),
    )
    assert_islist(ctx, v_pets, size=2)
    assert_isinstance(ctx, v_pets.getindex(0), 'Pet')
    assert_isinstance(ctx, v_pets.getindex(1), 'Pet')
    assert_eq(ctx, v_pets.getindex(0).getprop('name'), 'Basil')
    assert_eq(ctx, v_pets.getindex(1).getprop('name'), 'Billy')

    ctx.remark('Testing a method that *receives* a complex argument type')
    if demo_runner.lang == 'python':
        ctx.remark("XXX: this is not yet supported in python")
        ctx.remark("TODO: we can't pass dataclasses as args yet in python because python")
        ctx.remark("doesn't automatically json-encode dataclasses")
    else:
        v_check_arg = PanDict({}, CrossStr(), CrossAny())
        v_check_arg.addPair(pan('basil'), v_pets.getindex(0))
        v_check_arg.addPair(pan('billy'), v_pets.getindex(1))
        v_check = ctx.alsoDeclare('check', 'no_type', await_call(
            v_client.getprop('check_pets'),
            v_check_arg,
        ))
        assert_eq(ctx, v_check, 'pets_ok!')

    if ctx is not s:
        s.also(PanCall('test_body'))

    demo_runner.run_demo(s)


def test_generated_client_session_auth(demo_runner: DemoRunner) -> None:
    if demo_runner.lang == 'typescript':
        # TODO: we might need to implement this test anyway so that we can test raise vs return
        # XXX: Typescript test isn't strictly necessary here as browsers will support sessions by
        # default
        return

    if demo_runner.lang not in ('python', 'php'):
        raise Exception(f"Unexpected lang {demo_runner.lang!r}")

    s = Script()

    s.also(HardCodedStatement(
        php='require "get_client.php";',
        python=None,
    ))

    s.remark('load the client')
    s.alsoImportPy('get_client', ['get_client'])
    v_client = s.alsoDeclare('v_client', 'no_type', PanCall('get_client'))

    s.blank()
    s.remark('should return/raise an ApiUnauthorized first')
    s.alsoImportPy('generated_client', ['ApiUnauthorized'])
    _expect_error(
        demo_runner,
        s,
        PanCall(v_client.getprop('whoami')),
        'ApiUnauthorized',
        'Not logged in',
    )

    s.blank()
    s.remark('try an invalid username/password')
    assert_eq(
        s,
        PanCall(v_client.getprop('login'), pan("MrAnderson"), pan("secr3t")),
        'Invalid username or password',
    )

    s.remark('try missing credentials')
    assert_eq(
        s,
        PanCall(v_client.getprop('login'), pan(""), pan("secr3t")),
        'Username was empty',
    )

    s.blank()
    s.remark('confirm still not logged in')
    _expect_error(
        demo_runner,
        s,
        PanCall(v_client.getprop('whoami')),
        'ApiUnauthorized',
        'Not logged in',
    )

    s.remark('now log in with correct credentials')
    assert_eq(
        s,
        PanCall(v_client.getprop('login'), pan("neo"), pan("trinity")),
        pan(True),
    )
    assert_eq(
        s,
        PanCall(v_client.getprop('whoami')),
        pan('the_one'),
    )

    demo_runner.run_demo(s)


# TODO: also test
# - ApiBroken / ApiOutage
