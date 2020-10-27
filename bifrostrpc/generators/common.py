from typing import Iterator, Tuple

from paradox.generate.files import FileSpec
from paradox.generate.statements import ClassSpec


def appendFailureModeClasses(dest: FileSpec) -> None:
    dest.contents.remark('failure modes')
    for name, classspec in getFailureModeClasses():
        dest.contents.also(classspec)


def getFailureModeClasses() -> Iterator[Tuple[str, ClassSpec]]:
    af = ClassSpec(
        'ApiFailure',
        docstring=['parent class of all failure modes'],
        tsexport=True,
    )
    af.addProperty('message', str, initarg=True)
    yield 'ApiFailure', af

    yield 'ApiOutage', ClassSpec(
        'ApiOutage',
        bases=['ApiFailure'],
        tsbase='ApiFailure',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a network error prevents',
            'the method call succeeding. If a method fails with ApiOutage, you',
            'might possibly succeed on a retry.',
        ],
    )

    yield 'ApiBroken', ClassSpec(
        'ApiBroken',
        bases=['ApiFailure'],
        tsbase='ApiFailure',
        tsexport=True,
        docstring=[
            'returned (not thrown) by api methods when a bug prevents the method',
            'call from succeeding. It is unlikely you will get a successful',
            'result by retrying.',
        ]
    )
