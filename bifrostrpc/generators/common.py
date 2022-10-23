from paradox.generate.statements import ClassSpec
from paradox.interfaces import AcceptsStatements


def appendFailureModeClasses(dest: AcceptsStatements) -> None:
    dest.remark('failure modes')
    af = dest.also(ClassSpec(
        'ApiFailure',
        docstring=['parent class of all failure modes'],
        tsexport=True,
    ))
    af.addProperty('message', str, initarg=True)
    c_ApiOutage = dest.also(ClassSpec(
        'ApiOutage',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a network error prevents',
            'the method call succeeding. If a method fails with ApiOutage, you',
            'might possibly succeed on a retry.',
        ],
    ))
    c_ApiOutage.addPythonBaseClass('ApiFailure')
    c_ApiOutage.setPHPParentClass('ApiFailure')
    c_ApiOutage.setTypeScriptParentClass('ApiFailure')

    c_ApiBroken = dest.also(ClassSpec(
        'ApiBroken',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a bug prevents the method',
            'call from succeeding. It is unlikely you will get a successful',
            'result by retrying.',
        ]
    ))
    c_ApiBroken.addPythonBaseClass('ApiFailure')
    c_ApiBroken.setPHPParentClass('ApiFailure')
    c_ApiBroken.setTypeScriptParentClass('ApiFailure')
