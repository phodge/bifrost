from typing import Iterator, Tuple
from paradox.generate.statements import ClassSpec
from paradox.interfaces import AcceptsStatements


def appendFailureModeClasses(dest: AcceptsStatements, as_exception: bool) -> None:
    dest.remark('failure modes')
    for name, classspec in getFailureModeClasses(as_exception):
        dest.also(classspec)


def getFailureModeClasses(as_exception: bool) -> Iterator[Tuple[str, ClassSpec]]:
    af = ClassSpec(
        'ApiFailure',
        docstring=['parent class of all failure modes'],
        tsexport=True,
    )
    if as_exception:
        af.setPHPParentClass('Exception')
        af.addPythonBaseClass('Exception')
        # TODO: extending javascript's built-in Error class is not trivial and will require
        # specialised logic in the paradox project:
        # https://bobbyhadz.com/blog/typescript-extend-error-class
        af.setTypeScriptParentClass('__UNSUPPORTED__')
    else:
        af.addProperty('message', str, initarg=True)

    yield 'ApiFailure', af

    c_ApiOutage = ClassSpec(
        'ApiOutage',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a network error prevents',
            'the method call succeeding. If a method fails with ApiOutage, you',
            'might possibly succeed on a retry.',
        ],
    )
    c_ApiOutage.addPythonBaseClass('ApiFailure')
    c_ApiOutage.setPHPParentClass('ApiFailure')
    c_ApiOutage.setTypeScriptParentClass('ApiFailure')
    yield 'ApiOutage', c_ApiOutage

    c_ApiBroken = ClassSpec(
        'ApiBroken',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a bug prevents the method',
            'call from succeeding. It is unlikely you will get a successful',
            'result by retrying.',
        ]
    )
    c_ApiBroken.addPythonBaseClass('ApiFailure')
    c_ApiBroken.setPHPParentClass('ApiFailure')
    c_ApiBroken.setTypeScriptParentClass('ApiFailure')

    yield 'ApiBroken', c_ApiBroken

    c_ApiUnauthorized = ClassSpec(
        'ApiUnauthorized',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when valid authorization is'
            ' not provided',
        ]
    )
    c_ApiUnauthorized.addPythonBaseClass('ApiFailure')
    c_ApiUnauthorized.setPHPParentClass('ApiFailure')
    c_ApiUnauthorized.setTypeScriptParentClass('ApiFailure')
    yield 'ApiUnauthorized', c_ApiUnauthorized
