import dataclasses
import re
from typing import List, Optional, Tuple, cast

from paradox.expressions import pandict, tsexpr
from paradox.generate.files import FileTS
from paradox.generate.statements import ClassSpec, InterfaceSpec, RawTypescript
from paradox.typing import (CrossAny, CrossCallable, CrossNewType,
                            CrossTypeScriptOnlyType, dictof, unionof)

from bifrostrpc.generators import Names
from bifrostrpc.generators.common import appendFailureModeClasses
from bifrostrpc.typing import (Advanced, DataclassTypeSpec, DictTypeSpec,
                               FuncSpec, ListTypeSpec, LiteralTypeSpec,
                               NullTypeSpec, ScalarTypeSpec, TypeSpec,
                               UnionTypeSpec, _generateCrossType, getTypeSpec)

HEADER = 'generated by Bifrost RPC'

# allow looking up primitives by type or name
PRIMITIVES = {
    'str': 'string',
    'int': 'number',
    'bool': 'boolean',
}


def generateClient(
    dest: FileTS,
    *,
    classname: str,
    funcspecs: List[Tuple[str, FuncSpec]],
    adv: Advanced,
) -> None:
    # if the file already exists, make sure it was generated by us before destroying it
    # TODO: add a timestamp also

    firstline = dest.getfirstline()
    if firstline and firstline != f'// {HEADER}\n':
        raise Exception(f"Refusing to overwrite {dest.target}"
                        f"; it wasn't generated by Bifrost RPC")

    dest.filecomment(HEADER)

    appendFailureModeClasses(dest)
    _importExternalTypes(dest, adv)
    _generateAdvancedTypes(dest, adv)
    _generateWrappers(dest, classname, funcspecs, adv)

    dest.writefile()
    dest.makepretty()


def _importExternalTypes(dest: FileTS, adv: Advanced) -> None:
    for name, (tsmodule, ) in adv.getExternalTypeDetails():
        # XXX: dirty hack get rid of this
        if name in ('TagID', 'CategoryName', 'CategoryDesc', 'CategoryID'):
            continue
        dest.contents.alsoImportTS(tsmodule, [name])


def _generateAdvancedTypes(dest: FileTS, adv: Advanced) -> None:
    for name, baseType, children in adv.getNewTypeDetails():
        try:
            tsprimitive = PRIMITIVES[baseType.__name__]
        except KeyError:
            raise Exception(
                f'Cannot generate a typescript alias matching {name}'
                f'; no known primitive type for {baseType.__name__}')

        typeExpr = tsprimitive + ' & {readonly brand?: unique symbol}'
        if children:
            typeExpr = ' | '.join(children) + ' | (' + typeExpr + ')'

        dest.contents.blank()
        dest.contents.also(tsexpr(f'export type {name} = {typeExpr}'))

    for dc in adv.getAllDataclasses():
        dest.contents.blank()
        iface = InterfaceSpec(dc.__name__, tsexport=True, appendto=dest.contents)
        for field in dataclasses.fields(dc):
            generated = _generateCrossType(getTypeSpec(field.type, adv), adv)
            iface.addProperty(field.name, generated)


def _generateWrappers(
    dest: FileTS,
    classname: str,
    funcspecs: List[Tuple[str, FuncSpec]],
    adv: Advanced,
) -> None:
    cls = ClassSpec(
        classname,
        isabstract=True,
        tsexport=True,
        appendto=dest.contents,
    )

    # dispatch() function
    # FIXME: this should be protected, but we don't support that yet
    dispatchfn = cls.createMethod(
        'dispatch',
        CrossTypeScriptOnlyType('Promise<ApiFailure | any>'),
        isabstract=True,
    )
    # the method that should be called
    dispatchfn.addPositionalArg('method', str)
    # a dict of params to pass to the method
    dispatchfn.addPositionalArg('params', dictof(str, CrossAny()))
    # converter will be called with the result of the method call. It may modify result before
    # returning it. It may raise a TypeError if any part of result does not match the method's
    # return type.
    dispatchfn.addPositionalArg('converter', CrossCallable([CrossAny()], CrossAny()))

    for name, funcspec in funcspecs:
        argnames = funcspec.getArgSpecs().keys()
        retspec = funcspec.getReturnSpec()
        # TODO: need to ensure that FunctionSpec writes this out as a Promise<ApiFailure, ...> due
        # to the isasync=True kwarg
        rettype = unionof(CrossNewType('ApiFailure'), _generateCrossType(retspec, adv))

        fn = cls.createMethod(name, rettype, isasync=True)
        for argname, argspec in funcspec.getArgSpecs().items():
            fn.addPositionalArg(argname, _generateCrossType(argspec, adv))

        names = Names()

        argsdict = {argname: tsexpr(argname) for argname in argnames}
        fn.alsoDeclare('args', None, pandict(argsdict, CrossAny()))

        with fn.withRawTS() as ts:
            ts.rawline(f"const converter = (result: any) => {{")
            # verify that result matches the typespec for ret
            _generateConverter(ts, 'result', retspec, names, adv, '  ')
            ts.rawline(f'  return result;')
            ts.rawline(f'}};')
            ts.rawline(f"return await this.dispatch('{name}', args, converter);")


def _generateType(spec: TypeSpec, adv: Advanced) -> str:
    if isinstance(spec, NullTypeSpec):
        return 'null'

    if isinstance(spec, LiteralTypeSpec):
        if spec.expectedType is bool:
            raise Exception("TODO: test this code path")  # noqa
            return 'true' if spec.expected else 'false'  # pylint: disable=unreachable

        if spec.expectedType is int:
            raise Exception("TODO: test this code path")  # noqa
            return str(spec.expected)  # pylint: disable=unreachable

        if spec.expectedType is not str:
            raise Exception(f"Unexpected literal type {spec.expectedType.__name__}")

        if not re.match(r'^[a-zA-Z0-9_.,\-]+$', cast(str, spec.expected)):
            raise Exception(f"Literal {spec.expected!r} is too complex to rebuild in typescript")

        return '"' + cast(str, spec.expected) + '"'

    if isinstance(spec, ScalarTypeSpec):
        typeName = spec.typeName
        if adv.hasNewType(spec.originalType) or adv.hasExternalType(spec.originalType):
            return typeName

        try:
            return PRIMITIVES[typeName]
        except KeyError:
            raise Exception(
                f'Cannot generate a typescript alias matching {typeName}'
                f'; no known primitive type for {typeName}')

    if isinstance(spec, DataclassTypeSpec):
        if not adv.hasDataclass(spec.class_):
            raise Exception(
                f'Cannot generate a typescript type for unknown dataclass {spec.class_.__name__}')

        return spec.class_.__name__

    if isinstance(spec, ListTypeSpec):
        itemstr = _generateType(spec.itemSpec, adv)
        if re.match(r'^\w+$', itemstr):
            return itemstr + '[]'
        return 'Array<' + itemstr + '>'

    if isinstance(spec, UnionTypeSpec):
        return ' | '.join([_generateType(variantspec, adv)for variantspec in spec.variants])

    if isinstance(spec, DictTypeSpec):
        assert isinstance(spec.keySpec, ScalarTypeSpec) and spec.keySpec.scalarType is str
        keytype = _generateType(spec.keySpec, adv)
        valuetype = _generateType(spec.valueSpec, adv)
        return f"{{[k: {keytype}]: {valuetype}}}"

    raise Exception(f"TODO: generate a type for {spec!r}")


def _getTypeNoMatchExpr(var_or_prop: str, spec: TypeSpec) -> Optional[str]:
    if isinstance(spec, NullTypeSpec):
        return f"{var_or_prop} !== null"

    if isinstance(spec, ScalarTypeSpec):
        tsscalar = PRIMITIVES[spec.scalarType.__name__]
        return f'typeof {var_or_prop} !== "{tsscalar}"'

    if isinstance(spec, LiteralTypeSpec):
        # a literal type's type definition is identical to how you would write it as an expression
        valueexpr = _generateType(spec, Advanced())
        return f'{var_or_prop} !== {valueexpr}'

    if isinstance(spec, DataclassTypeSpec):
        # not possible
        return None

    if isinstance(spec, ListTypeSpec):
        # not possible
        return None

    raise Exception(f'TODO: no code to get a type-match expr for {spec!r}')


def _generateConverter(
    ts: RawTypescript,
    var_or_prop: str,
    spec: TypeSpec,
    names: Names,
    adv: Advanced,
    indent: str,
) -> None:
    if isinstance(spec, NullTypeSpec):
        # make sure the thing is null
        ts.rawline(f'{indent}if ({var_or_prop} !== null) {{')
        ts.rawline(f'{indent}  throw new TypeError("{var_or_prop} should be null");')
        ts.rawline(f'{indent}}}')
        return

    if isinstance(spec, ScalarTypeSpec):
        tsscalar = PRIMITIVES[spec.scalarType.__name__]

        # make sure the thing has the correct type
        ts.rawline(f'{indent}if (typeof {var_or_prop} !== "{tsscalar}") {{')
        ts.rawline(f'{indent}  throw new TypeError("{var_or_prop} should be of type {tsscalar}");')
        ts.rawline(f'{indent}}}')
        return

    if isinstance(spec, ListTypeSpec):
        # make sure the thing is an array
        ts.rawline(f'{indent}if (!Array.isArray({var_or_prop})) {{')
        ts.rawline(f'{indent}  throw new TypeError("{var_or_prop} should be an Array");')
        ts.rawline(f'{indent}}}')

        # make sure all items have the correct type
        itemspec = spec.itemSpec
        itemvar = names.getNewName(var_or_prop, 'item', False)
        # TODO: if we actually need to *convert* a type, then we probably need to use
        #   for (let idx in var) { itemvar = var[idx]; ... }
        # or possibly
        #   var = var.map(function(var_item) { return convert(var_item); })...
        ts.rawline(f'{indent}for (let {itemvar} of {var_or_prop}) {{')
        # TODO: also if we want to provide meaningful error messages, we really want to know the
        # idx of the item that was broken and include it in the error message
        _generateConverter(ts, itemvar, itemspec, names, adv, indent + '  ')
        ts.rawline(f'{indent}}}')
        return

    if isinstance(spec, DataclassTypeSpec):
        if not adv.hasDataclass(spec.class_):
            raise Exception(
                f'Cannot generate a typescript type for unknown dataclass {spec.class_.__name__}')

        ts.rawline(f"{indent}// make sure {var_or_prop} is an object that has properties")
        ts.rawline(f"{indent}if (!{var_or_prop}) {{")
        msg = f'{var_or_prop} must be an object that satisfies {spec.class_.__name__} interface'
        ts.rawline(f"{indent}  throw new TypeError('{msg}');")
        ts.rawline(f"{indent}}}")
        ts.rawline(f'{indent}// verify each member of {spec.class_.__name__}')
        for name, fieldspec in spec.fieldSpecs.items():
            propexpr = var_or_prop + '.' + name
            _generateConverter(ts, propexpr, fieldspec, names, adv, indent)
        return

    if isinstance(spec, UnionTypeSpec):
        # make a list of simple expressions that can be used to verify simple types quickly, and a
        # list of TypeSpecs for which simple expressions aren't possible
        notsimple: List[TypeSpec] = []
        simpleexprs: List[str] = []

        for vspec in spec.variants:
            nomatchexpr = _getTypeNoMatchExpr(var_or_prop, vspec)
            if nomatchexpr is None:
                notsimple.append(vspec)
            else:
                simpleexprs.append(nomatchexpr)

        joinedexpr = ' && '.join(simpleexprs)

        # if they were all simple, we can use a single negative-if to match invalid types
        # TODO: this won't work if we have no simpleexprs
        ts.rawline(f'{indent}if ({joinedexpr}) {{')
        # use a nested function for flow-control ... mostly so we can use 'return' statements
        # to break out of the function early if we find a matching type
        ts.rawline(f'{indent}  (function() {{')
        for vspec in notsimple:
            # add a try/except for each vspec
            for vspec in notsimple:
                ename = names.getNewName(var_or_prop, 'error', False)
                ts.rawline(f'{indent}    try {{')
                _generateConverter(ts, var_or_prop, vspec, names, adv, indent + '      ')
                ts.rawline(f'{indent}      return; // {var_or_prop} matches this variant')
                ts.rawline(f'{indent}    }} catch ({ename}) {{')
                ts.rawline(f'{indent}      if ({ename} instanceof TypeError) {{')
                ts.rawline(f'{indent}        // ignore type-error - continue on to next variant')
                ts.rawline(f'{indent}      }} else {{')
                ts.rawline(f'{indent}        throw {ename}; // re-throw any real errors')
                ts.rawline(f'{indent}      }}')
                ts.rawline(f'{indent}    }}')  # end try/catch
        ts.rawline(f'{indent}    throw new TypeError("{var_or_prop} did not match any variant");')
        ts.rawline(f'{indent}  }})();')
        ts.rawline(f'{indent}}}')
        return

    if isinstance(spec, DictTypeSpec):
        assert isinstance(spec.keySpec, ScalarTypeSpec) and spec.keySpec.scalarType is str

        # NOTE: we don't bother typechecking the keys since we know they will be strings coming
        # from JSON
        ts.rawline(f"{indent}// make sure {var_or_prop} is an object that matches the dict spec")
        ts.rawline(f"{indent}if (!{var_or_prop}) {{")
        msg = f'{var_or_prop} must be an object'
        ts.rawline(f"{indent}  throw new TypeError('{msg}');")
        ts.rawline(f"{indent}}}")
        ts.rawline(f'{indent}// verify each item of the dict')
        keyvar = names.getNewName(var_or_prop, 'key', False)
        ts.rawline(f'{indent}for (let {keyvar} in {var_or_prop}) {{')
        itemvar = var_or_prop + '[' + keyvar + ']'
        _generateConverter(ts, itemvar, spec.valueSpec, names, adv, indent + '  ')
        ts.rawline(f'{indent}}}')
        return

    raise Exception(f"TODO: generate a converter for {var_or_prop} using {spec!r}")
