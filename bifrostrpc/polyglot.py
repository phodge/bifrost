from contextlib import contextmanager
from typing import Dict, Iterable, Iterator, Optional, Tuple

from paradox.expressions import (PanExpr, PanVar, PHPPrecedence, PyPrecedence,
                                 TSPrecedence)
from paradox.generate.files import FileWriter
from paradox.generate.statements import (CatchBlock2, ImportSpecPHP,
                                         ImportSpecPy, ImportSpecTS,
                                         SimpleRaise, Statement, TryCatchBlock)
from paradox.interfaces import AcceptsStatements
from paradox.typing import CrossType

TYPE_ERROR_CLS = {
    "php": "UnexpectedValueException",
    "python": "TypeError",
}


def raiseTypeError(
    context: AcceptsStatements,
    *,
    pymsg: str = None,
    phpmsg: str = None,
    pyexpr: PanExpr = None,
    phpexpr: PanExpr = None,
) -> None:
    if pymsg or phpmsg:
        stmt = PolyglotRaise(
            TYPE_ERROR_CLS,
            messages={
                'php': phpmsg,
                'python': pymsg,
            }
        )
        assert pyexpr is None
        assert phpexpr is None
    else:
        assert pyexpr or phpexpr
        stmt = PolyglotRaise(
            TYPE_ERROR_CLS,
            exprs={
                'php': phpexpr,
                'python': pyexpr,
            }
        )
    context.also(stmt)


@contextmanager
def withCatchTypeError(
    context: TryCatchBlock,
    var: PanVar = None,
) -> Iterator[CatchBlock2]:
    with context.withCatchBlock2(
        var,
        pyclass=TYPE_ERROR_CLS['python'],
        phpclass=TYPE_ERROR_CLS['php'],
    ) as block:
        yield block


class PolyglotRaise(Statement):
    def __init__(
        self,
        ctors: Dict[str, str],
        *,
        messages: Dict[str, Optional[str]] = None,
        exprs: Dict[str, Optional[PanExpr]] = None,
    ) -> None:
        super().__init__()

        if messages:
            if 'python' in messages:
                self._pystmt = SimpleRaise(ctors['python'], msg=messages['python'])
            if 'php' in messages:
                self._phpstmt = SimpleRaise(ctors['php'], msg=messages['php'])
            if 'typescript' in messages:
                self._tsstmt = SimpleRaise(ctors['typescript'], msg=messages['typescript'])
        else:
            assert exprs is not None
            if 'python' in exprs:
                self._pystmt = SimpleRaise(ctors['python'], expr=exprs['python'])
            if 'php' in exprs:
                self._phpstmt = SimpleRaise(ctors['php'], expr=exprs['php'])
            if 'typescript' in exprs:
                self._tsstmt = SimpleRaise(ctors['typescript'], expr=exprs['typescript'])

    def writepy(self, w: FileWriter) -> int:
        return self._pystmt.writepy(w)

    def writets(self, w: FileWriter) -> None:
        self._tsstmt.writets(w)

    def writephp(self, w: FileWriter) -> None:
        self._phpstmt.writephp(w)

    def getImportsPy(self) -> Iterable[ImportSpecPy]:
        return self._pystmt.getImportsPy()

    def getImportsTS(self) -> Iterable[ImportSpecTS]:
        return self._tsstmt.getImportsTS()

    def getImportsPHP(self) -> Iterable[ImportSpecPHP]:
        return self._phpstmt.getImportsPHP()


class PolyglotExpr(PanExpr):
    def __init__(
        self,
        *,
        pyexpr: PanExpr = None,
        tsexpr: PanExpr = None,
        phpexpr: PanExpr = None,
    ) -> None:
        super().__init__()

        self._pyexpr = pyexpr
        self._tsexpr = tsexpr
        self._phpexpr = phpexpr

    def getPanType(self) -> CrossType:
        raise NotImplementedError("PolyglotExpr does not have typing implemented yet")

    def getPyExpr(self) -> Tuple[str, PyPrecedence]:
        if not self._pyexpr:
            raise Exception("PolyglotExpr does not have a pyexpr")
        return self._pyexpr.getPyExpr()

    def getTSExpr(self) -> Tuple[str, TSPrecedence]:
        if not self._tsexpr:
            raise Exception("PolyglotExpr does not have a tsexpr")
        return self._tsexpr.getTSExpr()

    def getPHPExpr(self) -> Tuple[str, PHPPrecedence]:
        if not self._phpexpr:
            raise Exception("PolyglotExpr does not have a phpexpr")
        return self._phpexpr.getPHPExpr()
