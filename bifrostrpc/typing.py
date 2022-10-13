import abc
import dataclasses
import sys
from dataclasses import is_dataclass
from typing import (TYPE_CHECKING, Any, Callable, Dict, Iterable, List,
                    Literal, NewType, Set, Tuple, Type, Union, cast,
                    get_type_hints)

from paradox.typing import (CrossBool, CrossCustomType, CrossDict, CrossList,
                            CrossLiteral, CrossNull, CrossNum, CrossStr,
                            CrossType, CrossUnion)

if TYPE_CHECKING:
    from paradox.expressions import PanExpr


ErrorList = List[str]
ScalarTypes = Union[Type[str], Type[int], Type[bool]]


if sys.version_info >= (3, 10, 0):
    # 3.10.0 onwards we can use a simple isinstance check
    def _isnewtype(sometype: Any) -> bool:
        # XXX: "type: ignore" is need here because NewType isn't a valid 2nd
        # arg for isinstance() until python3.10
        # pylint: disable=isinstance-second-argument-not-valid-type
        return isinstance(sometype, NewType)  # type: ignore
else:
    def _isnewtype(sometype: Any) -> bool:
        return isinstance(sometype, type(NewType))


class Advanced:
    """
    A collection of "advanced" types (NewType()s and dataclasses).

    This collection can be passed along to FuncSpec() and will enable the generated TypeSpecs to
    work with the more advanced types.
    """
    newTypes: Dict[str, Type[Any]]
    childTypes: Dict[str, List[str]]
    dataclasses: List[Type[Any]]
    contextTypes: Set[Type[Any]]
    authTypes: Set[Type[Any]]
    # {<newtype>: (<tsmodule>, )}
    externalTypes: Dict[Type[Any], Tuple[str, ]]

    def __init__(self) -> None:
        self.newTypes = {}
        self.dataclasses = []
        self.childTypes = {}
        self.contextTypes = set()
        self.authTypes = set()
        self.externalTypes = {}

    def addContextType(self, newType: Type[Any]) -> None:
        self.contextTypes.add(newType)

    def addAuthType(self, newType: Type[Any]) -> None:
        self.authTypes.add(newType)

    def addNewType(self, newType: Type[Any]) -> None:
        # it must be a NewType
        if not _isnewtype(newType):
            raise Exception(f'Not a NewType: {newType!r}')
        name = newType.__name__
        if name in self.newTypes:
            raise Exception(f'a NewType named {name!r} has already been added')
        self.newTypes[name] = newType

        # register ourselves as being children of our parent (if it is also a NewType)
        parent = newType.__supertype__
        if _isnewtype(parent):
            parentName = parent.__name__
            if parentName not in self.newTypes:
                raise Exception(
                    f'Cannot add NewType({name!r}): parent type {parentName!r} is unknown')
            self.childTypes.setdefault(parentName, []).append(name)

    def addExternalType(self, newType: Type[Any], *, tsmodule: str) -> None:
        # it must be a NewType
        if not _isnewtype(newType):
            raise Exception(f'Not a NewType: {newType!r}')

        assert newType not in self.externalTypes
        self.externalTypes[newType] = (tsmodule, )

    def addDataclass(self, class_: Type[Any]) -> None:
        if not is_dataclass(class_):
            raise TypeError(f'{class_!r} is not a dataclass')
        self.dataclasses.append(class_)

    def hasNewType(self, someType: Any) -> bool:
        try:
            name = someType._name  # pylint: disable=protected-access
        except AttributeError:
            name = someType.__name__
        return name in self.newTypes

    def hasExternalType(self, someType: Any) -> bool:
        return someType in self.externalTypes

    def hasContextType(self, someType: Type[Any]) -> bool:
        return someType in self.contextTypes

    def hasAuthType(self, someType: Type[Any]) -> bool:
        return someType in self.authTypes

    def hasDataclass(self, class_: Any) -> bool:
        return class_ in self.dataclasses

    def getNewTypeDetails(self) -> Iterable[Tuple[str, Type[Any], List[str]]]:
        for name, nt in self.newTypes.items():
            # typeName, supertype, resolvedType
            resolvedType = _resolveNewType(nt, self)[0]
            yield name, resolvedType, self.childTypes.get(name, [])

    def getExternalTypeDetails(self) -> Iterable[Tuple[str, Tuple[str, ]]]:
        for someType, (tsmodule, ) in self.externalTypes.items():
            yield someType.__name__, (tsmodule, )

    def getAllDataclasses(self) -> Iterable[Any]:
        yield from self.dataclasses


class FuncSpec:
    argSpecs: Dict[str, 'TypeSpec']
    retvalSpec: 'TypeSpec'
    contextvars: Dict[str, Type[Any]]
    authvars: Dict[str, Type[Any]]

    def __init__(self, fn: Callable[..., Any], adv: Advanced) -> None:
        self.contextvars = {}
        self.authvars = {}
        self.argSpecs = {}
        for name, someType in get_type_hints(fn).items():
            if adv.hasAuthType(someType):
                self.authvars[name] = someType
                continue
            if adv.hasContextType(someType):
                self.contextvars[name] = someType
                continue
            spec = getTypeSpec(someType, adv)
            if name == 'return':
                self.retvalSpec = spec
            else:
                self.argSpecs[name] = spec

    def importArgs(self, args: Any, label: str, errors: ErrorList) -> Dict[str, Any]:
        if not isinstance(args, dict):
            actualTypeName = _getActualTypeName(args)
            errors.append(f'label must be a dict; got {actualTypeName} instead')
            return {}

        transformed = {}
        for name, spec in self.argSpecs.items():
            itemlabel = f'{label}[{name!r}]'
            try:
                value = args[name]
            except KeyError:
                # TODO: allow *not* providing values for optional arguments
                errors.append(itemlabel + ' is required')
                continue

            transformed[name] = spec.getImported(value, itemlabel, errors)

        # also warn about extra args
        for name in args:
            if name not in self.argSpecs:
                itemlabel = f'{label}[{name!r}]'
                errors.append(f'Unexpected argument {itemlabel}')

        return transformed

    def getArgSpecs(self) -> Dict[str, 'TypeSpec']:
        return self.argSpecs

    def exportRetval(
        self,
        retval: Any,
        label: str,
        showdc: bool,
        errors: ErrorList,
    ) -> Any:
        return self.retvalSpec.getExported(retval, label, showdc, errors)

    def getReturnSpec(self) -> 'TypeSpec':
        return self.retvalSpec


class TypeSpec(abc.ABC):
    """
    Holds a type definition for an argument or return value.
    """
    @abc.abstractmethod
    def getImported(self, value: Any, label: str, errors: ErrorList) -> Any:
        ...

    @abc.abstractmethod
    def getExported(self, value: Any, label: str, showdc: bool, errors: ErrorList) -> Any:
        ...


def getTypeSpec(someType: Any, adv: Advanced) -> TypeSpec:
    from bifrostrpc import TypeNotSupportedError

    # resolve the type (in case it's a NewType) and also get its name
    realType, typeNames = _resolveNewType(someType, adv)
    typeName = typeNames[0]

    if realType is Any:
        raise TypeNotSupportedError("'typing.Any' is not a permitted type")

    # FIXME: not sure why we're getting E721 here
    if realType is type(None):  # noqa: E721
        return NullTypeSpec()

    if realType is str or realType is int or realType is bool:
        return ScalarTypeSpec(realType, typeName, someType)

    if is_dataclass(realType):
        if not adv.hasDataclass(realType):
            raise TypeError(f"Can't get TypeSpec for unknown dataclass {realType!r}")

        # create TypeSpecs for all the fields
        fieldSpecs: Dict[str, TypeSpec] = {}
        for f in dataclasses.fields(realType):
            fieldExporter = getTypeSpec(f.type, adv)
            fieldSpecs[f.name] = fieldExporter
        return DataclassTypeSpec(realType, fieldSpecs)

    # NOTE: this doesn't work under python 3.7 or python 3.8
    if isinstance(realType, type(Literal)) or getattr(realType, '__origin__', None) is Literal:
        if sys.version_info < (3, 7, 0):
            args = realType.__values__
        else:
            args = realType.__args__

        assert len(args) == 1
        value = args[0]
        if type(value) not in (str, int, bool):
            raise Exception('getTypeSpec(): Literal must contain a str, int or bool')

        # TODO: refactor LiteralTypeSpec so that it supports multiple literals like you'd expect
        return LiteralTypeSpec(value)

    if realType.__module__ != 'typing':
        raise Exception(f'getTypeSpec() will only work with types from typing module'
                        f'; type {realType!r} is not supported')

    if typeName == 'Optional':
        subType = realType.__args__[0]
        return UnionTypeSpec([getTypeSpec(subType, adv), NullTypeSpec()])

    if typeName == 'List':
        assert len(realType.__args__) == 1
        itemType = realType.__args__[0]
        itemSpec = getTypeSpec(itemType, adv)
        return ListTypeSpec(itemSpec)

    if typeName == 'Union':
        # get specs for the various types
        variants: List[TypeSpec] = []
        assert len(realType.__args__) >= 1
        for subType in realType.__args__:
            variants.append(getTypeSpec(subType, adv))
        return UnionTypeSpec(variants)

    if typeName == 'Dict':
        assert len(realType.__args__) == 2
        keyType, valueType = realType.__args__
        if keyType is str:
            keySpec = ScalarTypeSpec(str, 'str', str)
        else:
            # NOTE: we don't support non-string keys, but this isn't a big deal because our inputs
            # are always coming from JSON
            keyTypeName = keyType.__name__
            raise TypeNotSupportedError(
                f'getTypeSpec() only supports Dict[str, ...]; got Dict[{keyTypeName}, ...] instead'
            )
        valueSpec = getTypeSpec(valueType, adv)
        return DictTypeSpec(keySpec, valueSpec)

    raise TypeNotSupportedError(f'getTypeSpec(): typing.{typeName} is not supported')


class NullTypeSpec(TypeSpec):
    def getExported(self, value: Any, label: str, showdc: bool, errors: ErrorList) -> None:
        if value is not None:
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be None; got {actualTypeName} instead')
        return value

    def getImported(self, value: Any, label: str, errors: ErrorList) -> None:
        if value is not None:
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be Null; got {actualTypeName} instead')
        return value


def _getActualTypeName(value: Any) -> str:
    if value is None:
        return 'None'

    name = type(value).__name__
    article = 'an ' if name[0] in 'aeiouAEIOU' else 'a '
    return article + name


def _resolveNewType(someType: Any, adv: Advanced) -> Tuple[Any, List[str]]:
    if not _isnewtype(someType):
        if sys.version_info < (3, 7, 0):
            # python 3.6 (the earliest python we support) doesn't have the ._name attributes we
            # require below.
            if someType is Any:
                return someType, ['Any']

            if isinstance(someType, type(Literal)):
                return someType, ['Literal']

            # FIXME:
            # This is a pretty dirty hack - because python3.6 didn't have the ._name attribute yet,
            # we have to poke into the __doc__ to try and figure out what kind of type we're
            # looking at. This is prone to breaking with even just a minor python version update,
            # but thankfully we only need it for the 3.6 series, which is now in security-fix-only
            # mode (as per PEP 494)
            if (
                someType.__module__ == 'typing'
                and someType.__doc__
                and someType.__doc__.startswith('Union type;')
            ):
                # TODO: but does this work if you've wrapped it with a custom type?
                return someType, ['Union']

        # TODO: accessing someType.__name__ like this doesn't work if someType is a
        # forward-declaration (a string containing the type name)
        try:
            n = someType._name  # pylint: disable=protected-access
        except AttributeError:
            n = someType.__name__
        else:
            if n is None:
                # get origin type
                n = someType.__origin__._name  # pylint: disable=protected-access
        return someType, [n]

    # if the NewType isn't part of our Advanced list, then we're not allowed to resolve it
    if not adv.hasNewType(someType) and not adv.hasExternalType(someType):
        raise TypeError(f"Can't resolve unknown NewType {someType.__name__}")

    # if it *is* a newtype, resolve it as well
    resolvedType, resolvedNames = _resolveNewType(cast(Any, someType).__supertype__, adv)
    return resolvedType, [someType.__name__] + resolvedNames


class ListTypeSpec(TypeSpec):
    def __init__(self, itemSpec: TypeSpec):
        self.itemSpec = itemSpec

    def getExported(self, value: Any, label: str, showdc: bool, errors: ErrorList) -> List[Any]:
        if isinstance(value, (str, bytes)):
            typeName = type(value).__name__
            errors.append(f'Cowardly efusing to export {label} ({typeName}) as a list')
            return [value]

        # TODO is this the best way to detect if value is iterable?
        try:
            iter_ = (i for i in value)
        except TypeError:
            errors.append(f'{label} cannot be exported to a List as it is not iterable')
            return [value]

        ret = []
        for idx, item in enumerate(iter_):
            ret.append(self.itemSpec.getExported(item, f'{label}[{idx}]', showdc, errors))
        return ret

    def getImported(self, value: Any, label: str, errors: ErrorList) -> List[Any]:
        if type(value) is not list:  # pylint: disable=unidiomatic-typecheck
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be a list; got {actualTypeName} instead')
            return value

        ret = []
        for idx, item in enumerate(value):
            ret.append(self.itemSpec.getImported(item, f'{label}[{idx}]', errors))
        return ret


class UnionTypeSpec(TypeSpec):
    variants: List[TypeSpec]

    def __init__(self, variants: List[TypeSpec]):
        self.variants = variants

    def _process(
        self,
        value: Any,
        label: str,
        errors: ErrorList,
        transformer: Callable[[TypeSpec, Any, str, ErrorList], Any],
    ) -> Any:
        # try each of the variant specs until we find one that works
        allErrors: List[str] = []
        for i, spec in enumerate(self.variants):
            before = len(allErrors)
            variantLabel = f'{label} (variant #{i})'
            transformed = transformer(spec, value, variantLabel, allErrors)
            if len(allErrors) == before:
                # if there are no errors from this exporter, then use this transformed value
                return transformed

        # if all specs produced errors, push all the errors along with a summary
        num = len(self.variants)
        errors.append(f"{label} could not satisfy any of the union type's {num} variants")
        errors.extend(allErrors)
        return value

    def getExported(self, value: Any, label: str, showdc: bool, errors: ErrorList) -> Any:
        return self._process(
            value,
            label,
            errors,
            lambda spec, value, variantLabel, allErrors:
                spec.getExported(value, variantLabel, showdc, allErrors)
        )

    def getImported(self, value: Any, label: str, errors: ErrorList) -> Any:
        return self._process(
            value,
            label,
            errors,
            lambda spec, value, variantLabel, allErrors:
                spec.getImported(value, variantLabel, allErrors)
        )


class DictTypeSpec(TypeSpec):
    keySpec: TypeSpec
    valueSpec: TypeSpec

    def __init__(self, keySpec: TypeSpec, valueSpec: TypeSpec):
        self.keySpec = keySpec
        self.valueSpec = valueSpec

    def getExported(self, value: Any, label: str, showdc: bool, errors: ErrorList) -> Any:
        if type(value) is not dict:  # pylint: disable=unidiomatic-typecheck
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be a dict; got {actualTypeName} instead')
            return value

        transformed: Dict[Any, Any] = {}
        for k, v in value.items():
            valuelabel = label + '[' + repr(k) + ']'
            newKey = self.keySpec.getExported(k, label, showdc, errors)
            newVal = self.valueSpec.getExported(v, valuelabel, showdc, errors)
            transformed[newKey] = newVal
        return transformed

    def getImported(self, value: Any, label: str, errors: ErrorList) -> Any:
        if type(value) is not dict:  # pylint: disable=unidiomatic-typecheck
            # NOTE: we don't support importing dataclasses here because we're
            # not trying to convert sophisticated python types into primitive types
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be a dict; got {actualTypeName} instead')
            return value

        transformed: Dict[Any, Any] = {}
        for k, v in value.items():
            newKey = self.keySpec.getImported(k, label, errors)
            newVal = self.valueSpec.getImported(v, label + '[' + repr(k) + ']', errors)
            transformed[newKey] = newVal
        return transformed


class DataclassTypeSpec(TypeSpec):
    class_: Any
    fieldSpecs: Dict[str, TypeSpec]

    def __init__(self, class_: Any, fieldSpecs: Dict[str, TypeSpec]):
        self.class_ = class_
        self.fieldSpecs = fieldSpecs

    def getImported(self, value: Any, label: str, errors: ErrorList) -> Any:
        if not isinstance(value, dict):
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be a dict; got {actualTypeName} instead')
            return value

        # TODO: type-check all fields
        kwargs = {}
        for k, v in value.items():
            try:
                spec = self.fieldSpecs[k]
            except KeyError:
                errors.append(f'{label} contains unexpected key {k!r}')
                continue

            kwargs[k] = spec.getImported(v, f'{label}[{k!r}]', errors)

        for f in self.fieldSpecs:
            if f not in kwargs:
                # TODO: don't emit an error if the field has a default value
                errors.append(f'{label} is missing field {f!r}')

        try:
            return self.class_(**kwargs)
        except TypeError as e:
            errors.append(f'{label} error constructing {self.class_.__name__}: {e}')

        return None

    def getExported(
        self,
        value: Any,
        label: str,
        showdc: bool,
        errors: ErrorList,
    ) -> Dict[str, Any]:
        if not isinstance(value, self.class_):
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be an instance of {self.class_.__name__}'
                          f'; got {actualTypeName} instead')
            return value

        # NOTE: you *could* use dataclasses.asdict() to recursively turn `target` into a dict, but
        # then you wouldn't be recursively verifying types along the way.
        ret = {}
        for name, spec in self.fieldSpecs.items():
            fieldLabel = f'{label}.{name}'
            ret[name] = spec.getExported(getattr(value, name), fieldLabel, showdc, errors)
        if showdc:
            ret['__dataclass__'] = self.class_.__name__
        return ret


class ScalarTypeSpec(TypeSpec):
    # the primitive type
    scalarType: ScalarTypes

    # if the scalar type is a NewType, it will be the name of the new type. Otherwise, it is the
    # name of the primitive, e.g. "str"
    typeName: str

    # If the scalar type is a NewType, this will be the NewType instance. If it's a primitive type,
    # then this will be the primitive type.
    originalType: Type[Any]

    def __init__(self, scalarType: ScalarTypes, typeName: str, originalType: Type[Any]):
        self.scalarType = scalarType
        self.typeName = typeName
        self.originalType = originalType

    def getExported(self, value: Any, label: str, showdc: bool, errors: ErrorList) -> Any:
        # NOTE: for scalar values we don't actually transform (heaven forbid we should cast our
        # ints to strs automatically like PHP); we just warn on incorrect types
        if not isinstance(value, self.scalarType):
            actualTypeName = _getActualTypeName(value)
            errors.append(f'{label} must be of type {self.typeName}; got {actualTypeName} instead')
        return value

    # getImported() has the same implementation as getExported()
    def getImported(self, value: Any, label: str, errors: ErrorList) -> Any:
        return self.getExported(value, label, False, errors)

    def getMatchExpr(self, value: "PanExpr") -> "PanExpr":
        from paradox.expressions import isbool, isint, isstr

        if self.scalarType is str:
            return isstr(value)

        if self.scalarType is int:
            return isint(value)

        assert self.scalarType is bool
        return isbool(value)


class LiteralTypeSpec(TypeSpec):
    # TODO: this needs rewriting to support multiple Literal values
    expected: Union[str, int, bool]
    expectedType: Union[Type[str], Type[int], Type[bool]]

    def __init__(self, expected: Union[str, int, bool]) -> None:
        self.expected = expected
        self.expectedType = type(expected)

    @property
    def values(self) -> List[Union[str, int, bool]]:
        # TODO: get rid of self.expected in favour of having a true .values property
        return [self.expected]

    def getExported(
        self,
        value: Any,
        label: str,
        showdc: bool,
        errors: ErrorList,
    ) -> Union[str, int, bool]:
        if not (isinstance(value, self.expectedType) and value == self.expected):
            if type(value) in (str, int, bool, None):
                show = repr(value)
            else:
                show = _getActualTypeName(value)
            errors.append(f'{label} must be exactly {self.expected!r}; got {show} instead')
        return value

    # getImported() has the same implementation as getExported()
    def getImported(self, value: Any, label: str, errors: ErrorList) -> Any:
        return self.getExported(value, label, False, errors)


def _generateCrossType(
    spec: TypeSpec,
    adv: Advanced,
) -> CrossType:
    if isinstance(spec, NullTypeSpec):
        return CrossNull()

    if isinstance(spec, ScalarTypeSpec):
        if spec.typeName == "str":
            return CrossStr()
        if spec.typeName == "int":
            return CrossNum()
        if spec.typeName == "bool":
            return CrossBool()

        raise Exception("unreachable")

    if isinstance(spec, ListTypeSpec):
        return CrossList(_generateCrossType(spec.itemSpec, adv))

    if isinstance(spec, DictTypeSpec):
        keytype = _generateCrossType(spec.keySpec, adv)
        valuetype = _generateCrossType(spec.valueSpec, adv)
        return CrossDict(keytype, valuetype)

    if isinstance(spec, DataclassTypeSpec):
        if not adv.hasDataclass(spec.class_):
            raise Exception(
                f'Cannot generate a python type for unknown dataclass {spec.class_.__name__}')

        return CrossCustomType(
            python=spec.class_.__name__,
            typescript=spec.class_.__name__,
            phplang=spec.class_.__name__,
            phpdoc=spec.class_.__name__,
        )

    if isinstance(spec, UnionTypeSpec):
        return CrossUnion([
            _generateCrossType(variantspec, adv)
            for variantspec in spec.variants
        ])

    if isinstance(spec, LiteralTypeSpec):
        assert spec.expectedType in (bool, int, str)
        return CrossLiteral([spec.expected])

    raise Exception(f"TODO: generate a cross type for {spec!r}")
