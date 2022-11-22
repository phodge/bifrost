import dataclasses
import uuid
from typing import Any, List, Literal, Optional, Type

from paradox.expressions import (PanCall, PanDict, PanExpr, PanList, PanVar,
                                 and_, exacteq_, isbool, isdict, isint, islist,
                                 isnull, isstr, not_, pan, phpexpr, pyexpr)
from paradox.generate.statements import (AssignmentStatement, ClassSpec,
                                         ConditionalBlock, FunctionSpec,
                                         Statement, Statements)
from paradox.interfaces import AcceptsStatements
from paradox.typing import CrossAny, CrossCustomType, CrossStr

from bifrostrpc.generators import Names
from bifrostrpc.polyglot import raiseTypeError, withCatchTypeError
from bifrostrpc.typing import (Advanced, DataclassTypeSpec, DictTypeSpec,
                               ListTypeSpec, LiteralTypeSpec, NullTypeSpec,
                               ScalarTypeSpec, TypeSpec, UnionTypeSpec,
                               _generateCrossType, getTypeSpec)


class FilterNotPossible(Exception):
    pass


class ConverterNotPossible(Exception):
    pass


def getFilterBlock(
    var_or_prop: PanVar,
    label: str,
    *,
    spec: TypeSpec,
    names: Names,
    varianterror: bool = False,
    lang: Literal['python', 'php'],
) -> Statement:
    """
    Return a paradox Statement that will raise a TypeError on incorrect values.

    This method raises a FilterNotPossible exception if the TypeSpec doesnt support it (e.g. for
    Dataclasses).
    """
    def _raiseTypeError(context: AcceptsStatements, *, pymsg: str, phpmsg: str) -> None:
        if varianterror:
            raiseTypeError(
                context,
                pymsg=f"{label} did not match any variant",
                phpmsg=f"{label} did not match any variant",
            )
        else:
            raiseTypeError(
                context,
                pymsg=pymsg,
                phpmsg=phpmsg,
            )

    if isinstance(spec, NullTypeSpec):
        # just need a block that raises TypeError if the thing isn't None
        cond = ConditionalBlock(not_(isnull(var_or_prop)))
        _raiseTypeError(
            cond,
            pymsg=f"{label} must be None",
            phpmsg=f"{label} must be null",
        )
        return cond

    if isinstance(spec, ScalarTypeSpec):
        # just need to make sure the thing is an instance of the correct scalar type
        if spec.scalarType is str:
            expr_compare = isstr(var_or_prop)
            msg = f"{label} must be a string"
        elif spec.scalarType is int:
            expr_compare = isint(var_or_prop)
            msg = f"{label} must be an integer"
        elif spec.scalarType is bool:
            expr_compare = isbool(var_or_prop)
            msg = f"{label} must be a boolean"
        else:
            # unreachable
            raise Exception(f'Unexpected scalarType {spec.scalarType!r}')

        cond = ConditionalBlock(not_(expr_compare))
        _raiseTypeError(
            cond,
            pymsg=msg,
            phpmsg=msg,
        )
        return cond

    if isinstance(spec, ListTypeSpec):
        ret = Statements()

        # make sure the thing came back as a list
        with ret.withCond(not_(islist(var_or_prop))) as cond:
            _raiseTypeError(
                cond,
                pymsg=f"{label} must be a list",
                phpmsg=f"{label} must be an Array",
            )

        # run a filter over all items
        itemspec = spec.itemSpec
        v_item = names.getNewName2(var_or_prop.rawname, 'item', False)
        with ret.withFor(v_item, var_or_prop) as loop:
            # TODO: also if we want to provide meaningful error messages, we really want to know
            # the idx of the item that was broken and include it in the error message
            loop.also(getFilterBlock(
                v_item,
                f"{label}[$n]",
                spec=itemspec,
                names=names,
                lang=lang,
            ))

        return ret

    if isinstance(spec, DictTypeSpec):
        ret = Statements()

        # make sure the thing came back as a dict
        with ret.withCond(not_(isdict(var_or_prop))) as cond:
            _raiseTypeError(
                cond,
                pymsg=f"{label} must be of a dict",
                phpmsg=f"{label} must be an Array",
            )

        # make sure all dict keys/values have the correct type
        keyspec = spec.keySpec
        assert isinstance(keyspec, ScalarTypeSpec)
        assert keyspec.originalType is str
        valuespec = spec.valueSpec
        v_value = names.getNewName2(var_or_prop.rawname, 'value', False)

        with ret.withDictIter(var_or_prop, v_value) as loop2:
            # TODO: also if we want to provide meaningful error messages, we really want to know
            # the key of the item that was broken and include it in the error message
            loop2.also(getFilterBlock(
                v_value,
                f"{label}[$key]",
                spec=valuespec,
                names=names,
                lang=lang,
            ))

        return ret

    if isinstance(spec, UnionTypeSpec):
        # make a list of simple expressions that can be used to verify simple types quickly, and a
        # list of TypeSpecs for which simple expressions aren't possible
        simpleexprs: List[PanExpr] = []

        for vspec in spec.variants:
            nomatchexpr = _getTypeNoMatchExpr(var_or_prop, vspec, lang=lang)
            if nomatchexpr is None:
                raise FilterNotPossible(
                    "UnionTypeSpec contains non-simple values and needs a converter block"
                )

            simpleexprs.append(nomatchexpr)

        assert simpleexprs

        # if they were all simple, we can use a single negative-if to rule out some invalid types
        ret = Statements()

        with ret.withCond(and_(*simpleexprs)) as cond:
            _raiseTypeError(
                cond,
                pymsg=f"{label} did not match any variant",
                phpmsg=f"{label} did not match any variant",
            )

        return ret

    raise FilterNotPossible(
        f"Not possible to build a Filter block for {spec}"
    )


def _getTypeNoMatchExpr(
    var_or_prop: PanExpr,
    spec: TypeSpec,
    *,
    lang: Literal['php', 'python'],
) -> Optional[PanExpr]:
    if isinstance(spec, NullTypeSpec):
        return not_(isnull(var_or_prop))

    if isinstance(spec, ScalarTypeSpec):
        return not_(spec.getMatchExpr(var_or_prop))

    if isinstance(spec, LiteralTypeSpec):
        comparisons = [
            not_(exacteq_(var_or_prop, value))
            for value in spec.values
        ]
        return and_(*comparisons)

    if isinstance(spec, UnionTypeSpec):
        exprs = []
        for subspec in spec.variants:
            nomatchexpr = _getTypeNoMatchExpr(var_or_prop, subspec, lang=lang)
            if not nomatchexpr:
                # not possible for this Union type
                return None
            exprs.append(nomatchexpr)
        return and_(*exprs)

    if isinstance(spec, ListTypeSpec):
        if lang == 'python' and isinstance(spec.itemSpec, NullTypeSpec):
            return pyexpr(f'any(x is not None for x in {var_or_prop.getPyExpr()[0]})')

        itemSpec = spec.itemSpec
        if lang == 'python' and isinstance(itemSpec, ScalarTypeSpec):
            scalarName = itemSpec.scalarType.__name__
            return pyexpr(
                f'not all(isinstance(x, {scalarName}) for x in {var_or_prop.getPyExpr()[0]})',
            )

        # not possible
        return None

    if isinstance(spec, DataclassTypeSpec):
        # not possible
        return None

    if isinstance(spec, DictTypeSpec):
        # FIXME: this should actually be possible in some circumstances using any() and a list
        # comprehension
        return None

    raise Exception(f"Unexpected TypeSpec {spec!r}")


def getConverterExpr(
    var_or_prop: PanVar,
    *,
    label: str,
    spec: TypeSpec,
    adv: Advanced,
    lang: Literal['python', 'php'],
) -> PanExpr:
    # TODO: when the language is Python, we *can* get a converter exprfor
    # ListTypeSpec and DictTypeSpec by generating a python list comprehension
    # or dict comprehension (assuming converter expressions are possible for
    # all sub-types)

    if isinstance(spec, DataclassTypeSpec):
        if not adv.hasDataclass(spec.class_):
            raise Exception(
                f'Cannot generate a converter for unknown dataclass {spec.class_.__name__}')

        # TODO: build a generic static-method-call for paradox to avoid this stuff
        if lang == 'python':
            constructor = f'{spec.class_.__name__}.fromDict'
        elif lang == 'php':
            constructor = f'{spec.class_.__name__}::fromDict'
        else:
            raise NotImplementedError(f"TODO: add support for lang {lang!r} here")

        return PanCall(
            constructor,
            var_or_prop,
            pan(label),
        )

    raise ConverterNotPossible(f"A converter expression for {spec!r} not possible")


def getConverterBlock(
    var_or_prop: PanVar,
    v_out: PanVar,
    *,
    label: str,
    spec: TypeSpec,
    names: Names,
    adv: Advanced,
    hoistcontext: AcceptsStatements,
    lang: Literal['python', 'php'],
    varianterror: bool = False,
) -> Statement:
    """
    Return a paradox Statement that will convert var_or_prop to the right type.

    The converted value is assigned to `v_out`. A TypeError is raised by the generated code block
    if `var_or_prop` can't be converted.
    """
    assert names.isAssignable(v_out.rawname)
    assert v_out.rawname != var_or_prop.rawname

    try:
        converterexpr = getConverterExpr(
            var_or_prop=var_or_prop,
            label=label,
            spec=spec,
            adv=adv,
            lang=lang,
        )
        return AssignmentStatement(v_out, converterexpr)
    except ConverterNotPossible:
        pass

    def _raiseTypeError(context: Statements, *, pymsg: str, phpmsg: str) -> None:
        if varianterror:
            raiseTypeError(
                context,
                pymsg=f"{label} did not match any variant",
                phpmsg=f"{label} did not match any variant",
            )
        else:
            raiseTypeError(
                context,
                pymsg=pymsg,
                phpmsg=phpmsg,
            )

    if isinstance(spec, ListTypeSpec):
        ret = Statements()

        # make sure the thing came back as a list
        with ret.withCond(not_(islist(var_or_prop))) as cond:
            _raiseTypeError(
                cond,
                pymsg=f"{label} must be a list",
                phpmsg=f"{label} must be an Array",
            )

        ret.alsoAssign(v_out, PanList([], CrossAny()))

        # add converts for the items - we know filter blocks aren't possible because if they were,
        # we wouldn't be using getConverterBlock on this ListTypeSpec
        itemspec = spec.itemSpec
        v_item = names.getNewName2(var_or_prop.rawname, 'item', False)
        with ret.withFor(v_item, var_or_prop) as loop:
            # TODO: also if we want to provide meaningful error messages, we really want to know
            # the idx of the item that was broken and include it in the error message
            try:
                converterexpr = getConverterExpr(
                    v_item,
                    label=f"{label}[$n]",
                    spec=itemspec,
                    adv=adv,
                    lang=lang,
                )
            except ConverterNotPossible:
                v_item_converted = names.getNewName2(
                    var_or_prop.rawname,
                    'item_converted',
                    True,
                    type=CrossAny(),
                )
                converterblock = getConverterBlock(
                    v_item,
                    v_item_converted,
                    label=f"{label}[$n]",
                    spec=itemspec,
                    names=names,
                    adv=adv,
                    hoistcontext=hoistcontext,
                    lang=lang,
                )
                loop.also(converterblock)
                converterexpr = v_item_converted
            loop.alsoAppend(v_out, converterexpr)

        return ret

    if isinstance(spec, DictTypeSpec):
        ret = Statements()

        # make sure the thing came back as a list
        with ret.withCond(not_(isdict(var_or_prop))) as cond:
            _raiseTypeError(
                cond,
                pymsg=f"{label} must be a dict",
                phpmsg=f"{label} must be an Array",
            )

        ret.alsoAssign(v_out, PanDict({}, CrossStr(), CrossAny()))

        # add conversions for the items - we know filter blocks aren't possible because if they
        # were, we wouldn't be using getConverterBlock on this DictTypeSpec
        valuespec = spec.valueSpec
        valuetype = _generateCrossType(valuespec, adv=adv)
        keyspec = spec.keySpec
        assert isinstance(keyspec, ScalarTypeSpec)
        assert keyspec.scalarType is str
        v_val = names.getNewName2(var_or_prop.rawname, 'val', False)
        v_key = names.getNewName2(var_or_prop.rawname, 'key', False)
        with ret.withDictIter(var_or_prop, v_val, v_key) as loop3:
            # TODO: also if we want to provide meaningful error messages, we really want to know
            # the key of the item that was broken and include it in the error message
            try:
                converterexpr = getConverterExpr(
                    v_val,
                    label=f"{label}[$key]",
                    spec=valuespec,
                    adv=adv,
                    lang=lang,
                )
            except ConverterNotPossible:
                v_val_converted = names.getNewName2(
                    var_or_prop.rawname,
                    'val_converted',
                    True,
                    type=valuetype,
                )
                converterblock = getConverterBlock(
                    v_val,
                    v_val_converted,
                    label=f"{label}[$key]",
                    spec=valuespec,
                    names=names,
                    adv=adv,
                    hoistcontext=hoistcontext,
                    lang=lang,
                )
                loop3.also(converterblock)
                converterexpr = v_val_converted
            loop3.alsoAssign(v_out.getitem(v_key), converterexpr)

        return ret

    if isinstance(spec, UnionTypeSpec):
        return _getUnionConverterBlock(
            var_or_prop,
            v_out,
            spec=spec,
            names=names,
            adv=adv,
            label=label,
            hoistcontext=hoistcontext,
            lang=lang,
        )

    raise Exception(
        f"No code to generate a converter block for {var_or_prop} using {spec!r}"
    )


def _getUnionConverterBlock(
    var_or_prop: PanVar,
    v_out: PanVar,
    *,
    label: str,
    spec: UnionTypeSpec,
    names: Names,
    adv: Advanced,
    hoistcontext: AcceptsStatements,
    lang: Literal['python', 'php'],
) -> Statements:
    ret = Statements()

    # make a list of simple expressions that can be used to verify simple
    # types quickly, a list of expressions that can be used to convert into
    # a target type (usually this means to unpack a Dataclass from a dict),
    # and a list of code blocks (Statements instance) that can be used to
    # convert into a target type.
    excludeexprs: List[PanExpr] = []
    complexvariants: List[TypeSpec] = []

    for vspec in spec.variants:
        nomatchexpr = _getTypeNoMatchExpr(var_or_prop, vspec, lang=lang)
        if nomatchexpr is not None:
            excludeexprs.append(nomatchexpr)
        else:
            complexvariants.append(vspec)

    # if there were excludeexprs, then we can use a single negative-if to
    # quickly exclude some known good types from filtering/converting
    if excludeexprs:
        cond = ConditionalBlock(and_(*excludeexprs))
        with cond.withElse() as elseblock:
            elseblock.alsoAssign(v_out, var_or_prop)
        innerstmt: Statements = cond
        ret.also(innerstmt)
    else:
        innerstmt = ret

    if not complexvariants:
        # this should be impossible - a UnionTypeSpec with no complex variants would have been
        # handled already using a filter block from getFilterBlock().
        raiseTypeError(
            innerstmt,
            pymsg=f"{label} did not match any variant",
            phpmsg=f"{label} did not match any variant",
        )
        return ret

    # if there is only one complex variant, we can just throw its one block into the innerstmt
    if len(complexvariants) == 1:
        innerstmt.also(getFilterOrConverterBlock(
            var_or_prop,
            v_out,
            spec=complexvariants[0],
            names=names,
            adv=adv,
            label=label,
            hoistcontext=hoistcontext,
            lang=lang,
        ))
        return ret

    # if there are only two complex variants, we can put them into a try/catch
    if len(complexvariants) == 2:
        block1 = getFilterOrConverterBlock(
            var_or_prop,
            v_out,
            spec=complexvariants[0],
            names=names,
            adv=adv,
            label=label,
            hoistcontext=hoistcontext,
            lang=lang,
        )
        block2 = getFilterOrConverterBlock(
            var_or_prop,
            v_out,
            spec=complexvariants[1],
            names=names,
            adv=adv,
            label=label,
            hoistcontext=hoistcontext,
            lang=lang,
        )
        with innerstmt.withTryBlock() as tryblock:
            tryblock.also(block1)
            with withCatchTypeError(tryblock) as catchblock:
                catchblock.also(block2)
        return ret

    # the most complex Unions will require a 'checker' function - mostly so that we can
    v_checker_arg = names.getNewName2('', 'value', False)
    checkername = names.getSpecificName('_checker_' + uuid.uuid4().hex[:10], False).rawname
    innercheck = FunctionSpec(checkername, CrossAny())
    innercheck.addPositionalArg(v_checker_arg.rawname, CrossAny())
    innerstmt.alsoAssign(v_out, PanCall(checkername, var_or_prop))

    # add the anonymous function to the 'hoist context' - the outermost
    # function which it should be scoped into
    hoistcontext.also(innercheck)

    v_checker_out = names.getNewName2('', 'value', True)

    for vspec in complexvariants:
        with innercheck.withTryBlock() as tryblock:
            try:
                tryblock.also(getFilterBlock(
                    v_checker_arg,
                    label=label,
                    spec=vspec,
                    names=names,
                    varianterror=True,
                    lang=lang,
                ))
                tryblock.alsoReturn(v_checker_arg)
            except FilterNotPossible:
                try:
                    tryblock.alsoReturn(getConverterExpr(
                        v_checker_arg,
                        label=label,
                        spec=vspec,
                        adv=adv,
                        lang=lang,
                    ))
                except ConverterNotPossible:
                    tryblock.also(getConverterBlock(
                        v_checker_arg,
                        v_checker_out,
                        label=label,
                        spec=vspec,
                        names=names,
                        adv=adv,
                        hoistcontext=hoistcontext,
                        varianterror=True,
                        lang=lang,
                    ))
                    tryblock.alsoReturn(v_checker_out)

        with withCatchTypeError(tryblock) as catchblock:
            catchblock.remark('ignore TypeError - contine on to next variant')

    raiseTypeError(
        innercheck,
        pymsg=f"{label} did not match any variant",
        phpmsg=f"{label} did not match any variant",
    )
    return ret


def getFilterOrConverterBlock(
    var_or_prop: PanVar,
    v_out: PanVar,
    *,
    label: str,
    spec: TypeSpec,
    names: Names,
    adv: Advanced,
    hoistcontext: AcceptsStatements,
    lang: Literal['python', 'php'],
    varianterror: bool = False,
) -> Statement:
    try:
        return getFilterBlock(
            var_or_prop,
            label=label,
            spec=spec,
            names=names,
            lang=lang,
            varianterror=varianterror,
        )
    except FilterNotPossible:
        return getConverterBlock(
            var_or_prop,
            v_out=v_out,
            label=label,
            spec=spec,
            names=names,
            adv=adv,
            hoistcontext=hoistcontext,
            lang=lang,
            varianterror=varianterror,
        )


def getDataclassSpec(
    dc: Type[Any],
    *,
    adv: Advanced,
    lang: Literal['python', 'php'],
    hoistcontext: AcceptsStatements,
) -> ClassSpec:
    name = dc.__name__
    cls = ClassSpec(name, pydataclass=True)

    for field in dataclasses.fields(dc):
        fieldspec = getTypeSpec(field.type, adv)
        cls.addProperty(
            field.name,
            _generateCrossType(fieldspec, adv),
            initarg=True,
            tsreadonly=True,
        )

    # the dataclass needs a deserialization method, too
    fromdict = cls.createMethod(
        'fromDict',
        CrossCustomType(python=name, typescript=name, phplang=name, phpdoc=name),
        isstaticmethod=True,
    )
    v_data = fromdict.addPositionalArg('data', CrossAny())
    fromdict.addPositionalArg('label', str)

    # constructor part 1 - ensure the provided data is a dict
    with fromdict.withCond(not_(isdict(v_data))) as cond:
        raiseTypeError(
            cond,
            pyexpr=pyexpr('f"{label} must be a dict"'),
            phpexpr=phpexpr('"$label must be an Array"'),
        )

    # constructor part 2 - ensure the __dataclass__ item is present
    expr_dataclass = v_data.getitem('__dataclass__', pan(None))
    with fromdict.withCond(not_(exacteq_(expr_dataclass, pan(name)))) as cond:
        # Tell pylint not to worry about the use of %-string formatting here -
        # using an f-string to generate an f-string is too error prone:
        # pylint: disable=C0209
        raiseTypeError(
            cond,
            pyexpr=pyexpr('f"{label}[\'__dataclass__\'] must be \'%s\'"' % (name, )),
            phpexpr=phpexpr('"{$label}[\'__dataclass__\'] must be \'%s\'"' % (name, )),
        )

    names = Names()

    buildargs: List[PanExpr] = []

    # validate each property item
    for field in dataclasses.fields(dc):
        fname = field.name
        v_var = names.getNewName2('', fname, True, type=CrossAny())
        fromdict.alsoDeclare(v_var, None, v_data.getitem(fname, pan(None)))

        fieldspec = getTypeSpec(field.type, adv)

        # check the local variable's type
        try:
            fromdict.also(getFilterBlock(
                v_var,
                label=f"data[{fname!r}]",
                spec=fieldspec,
                names=names,
                lang=lang,
            ))
            buildargs.append(v_var)
        except FilterNotPossible:
            v_converted = names.getNewName2(v_var.rawname, 'converted', True, type=CrossAny())
            fromdict.also(getConverterBlock(
                v_var,
                v_converted,
                label=f"data[{fname!r}]",
                spec=fieldspec,
                names=names,
                adv=adv,
                hoistcontext=hoistcontext,
                lang=lang,
            ))
            buildargs.append(v_converted)

    fromdict.alsoReturn(PanCall.callClassConstructor(name, *buildargs))

    return cls
