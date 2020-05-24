from paradox.generate.files import FileSpec
from paradox.generate.statements import ClassSpec


def appendFailureModeClasses(dest: FileSpec) -> None:
    dest.contents.remark('failure modes')
    af = ClassSpec(
        'ApiFailure',
        docstring=['parent class of all failure modes'],
        appendto=dest.contents,
        tsexport=True,
    )
    af.addProperty('message', str, initarg=True)
    dest.contents.also(ClassSpec(
        'ApiOutage',
        bases=['ApiFailure'],
        tsbase='ApiFailure',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a network error prevents',
            'the method call succeeding. If a method fails with ApiOutage, you',
            'might possibly succeed on a retry.',
        ],
    ))
    dest.contents.also(ClassSpec(
        'ApiBroken',
        bases=['ApiFailure'],
        tsbase='ApiFailure',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a bug prevents the method',
            'call from succeeding. It is unlikely you will get a successful',
            'result by retrying.',
        ]
    ))
