from typing import Any, Callable, Dict, List, NewType, Optional, Type, Union

from pytest import raises  # type: ignore

try:
    from typing import Literal  # type: ignore
except ImportError:
    # Literal wasn't part of stdlib until 3.8
    from typing_extensions import Literal


def test_get_int_type_spec() -> None:
    from bifrostrpc.typing import Advanced
    from bifrostrpc.typing import getTypeSpec
    from bifrostrpc.typing import ScalarTypeSpec

    adv = Advanced()

    ts = getTypeSpec(int, adv)
    assert isinstance(ts, ScalarTypeSpec)
    assert ts.scalarType is int
    assert ts.originalType is int
    assert ts.typeName == 'int'

    MyInt = NewType('MyInt', int)
    adv.addNewType(MyInt)

    ts = getTypeSpec(MyInt, adv)
    assert isinstance(ts, ScalarTypeSpec)
    assert ts.scalarType is int
    assert ts.originalType is MyInt
    assert ts.typeName == 'MyInt'

    MyInt2 = NewType('MyInt2', MyInt)
    adv.addNewType(MyInt2)

    ts = getTypeSpec(MyInt2, adv)
    assert isinstance(ts, ScalarTypeSpec)
    assert ts.scalarType is int
    assert ts.originalType is MyInt2
    assert ts.typeName == 'MyInt2'


def test_get_str_type_spec() -> None:
    from bifrostrpc.typing import Advanced
    from bifrostrpc.typing import getTypeSpec
    from bifrostrpc.typing import ScalarTypeSpec

    adv = Advanced()

    ts = getTypeSpec(str, adv)
    assert isinstance(ts, ScalarTypeSpec)
    assert ts.scalarType is str
    assert ts.originalType is str
    assert ts.typeName == 'str'

    MyStr = NewType('MyStr', str)
    adv.addNewType(MyStr)

    ts = getTypeSpec(MyStr, adv)
    assert isinstance(ts, ScalarTypeSpec)
    assert ts.scalarType is str
    assert ts.originalType is MyStr
    assert ts.typeName == 'MyStr'

    MyStr2 = NewType('MyStr2', MyStr)
    adv.addNewType(MyStr2)

    ts = getTypeSpec(MyStr2, adv)
    assert isinstance(ts, ScalarTypeSpec)
    assert ts.scalarType is str
    assert ts.originalType is MyStr2
    assert ts.typeName == 'MyStr2'


def test_get_List_type_spec() -> None:
    from bifrostrpc import TypeNotSupportedError
    from bifrostrpc.typing import Advanced
    from bifrostrpc.typing import ListTypeSpec
    from bifrostrpc.typing import ScalarTypeSpec
    from bifrostrpc.typing import getTypeSpec

    # test handling of a simple List[int]
    ts = getTypeSpec(List[int], Advanced())
    assert isinstance(ts, ListTypeSpec)

    assert isinstance(ts.itemSpec, ScalarTypeSpec)
    assert ts.itemSpec.scalarType is int
    assert ts.itemSpec.originalType is int
    assert ts.itemSpec.typeName == 'int'

    # test handling of a more complex List[List[CustomType]]
    MyStr = NewType('MyStr', str)
    MyStr2 = NewType('MyStr2', MyStr)
    adv = Advanced()
    adv.addNewType(MyStr)
    adv.addNewType(MyStr2)
    ts = getTypeSpec(List[List[MyStr2]], adv)
    assert isinstance(ts, ListTypeSpec)
    assert isinstance(ts.itemSpec, ListTypeSpec)
    assert isinstance(ts.itemSpec.itemSpec, ScalarTypeSpec)
    assert ts.itemSpec.itemSpec.scalarType is str
    assert ts.itemSpec.itemSpec.originalType is MyStr2
    assert ts.itemSpec.itemSpec.typeName == 'MyStr2'

    UserID = NewType('UserID', int)
    Users = NewType('Users', List[UserID])
    adv = Advanced()
    adv.addNewType(UserID)
    adv.addNewType(Users)

    # TODO: we don't yet support a NewType wrapping a List like this
    with raises(TypeNotSupportedError):
        ts = getTypeSpec(Users, adv)
        assert isinstance(ts, ListTypeSpec)
        assert isinstance(ts.itemSpec, ListTypeSpec)
        assert isinstance(ts.itemSpec.itemSpec, ScalarTypeSpec)
        assert ts.itemSpec.itemSpec.scalarType is UserID
        assert ts.itemSpec.itemSpec.originalType is int
        assert ts.itemSpec.itemSpec.typeName == 'UserID'


def test_get_Dict_type_spec() -> None:
    from bifrostrpc import TypeNotSupportedError
    from bifrostrpc.typing import Advanced
    from bifrostrpc.typing import DictTypeSpec
    from bifrostrpc.typing import ScalarTypeSpec
    from bifrostrpc.typing import getTypeSpec

    # test handling of a simple Dict[str, int]
    ts = getTypeSpec(Dict[str, int], Advanced())
    assert isinstance(ts, DictTypeSpec)

    assert isinstance(ts.keySpec, ScalarTypeSpec)
    assert ts.keySpec.scalarType is str
    assert ts.keySpec.originalType is str
    assert ts.keySpec.typeName == 'str'

    assert isinstance(ts.valueSpec, ScalarTypeSpec)
    assert ts.valueSpec.scalarType is int
    assert ts.valueSpec.originalType is int
    assert ts.valueSpec.typeName == 'int'

    # test handling of a more complex Dict[str, Dict[str, CustomType]]
    MyStr = NewType('MyStr', str)
    MyStr2 = NewType('MyStr2', MyStr)
    adv = Advanced()
    adv.addNewType(MyStr)
    adv.addNewType(MyStr2)
    ts = getTypeSpec(Dict[str, Dict[str, MyStr2]], adv)
    assert isinstance(ts, DictTypeSpec)
    assert isinstance(ts.keySpec, ScalarTypeSpec)
    assert isinstance(ts.valueSpec, DictTypeSpec)
    assert isinstance(ts.valueSpec.keySpec, ScalarTypeSpec)
    assert isinstance(ts.valueSpec.valueSpec, ScalarTypeSpec)
    assert ts.keySpec.scalarType is str
    assert ts.keySpec.originalType is str
    assert ts.keySpec.typeName is 'str'
    assert ts.valueSpec.keySpec.scalarType is str
    assert ts.valueSpec.keySpec.originalType is str
    assert ts.valueSpec.keySpec.typeName is 'str'
    assert ts.valueSpec.valueSpec.scalarType is str
    assert ts.valueSpec.valueSpec.originalType is MyStr2
    assert ts.valueSpec.valueSpec.typeName == 'MyStr2'

    with raises(TypeNotSupportedError):
        getTypeSpec(Dict[MyStr2, str], adv)


def is_null_spec(ts: Any) -> bool:
    from bifrostrpc.typing import NullTypeSpec
    return isinstance(ts, NullTypeSpec)


def ScalarTester(
    originalType: Type[Any],
    scalarType: Union[Type[str], Type[int], Type[bool]],
    typeName: str,
) -> Callable[[Any], bool]:
    """
    Return a callable that tests whether a given TypeSpec is a ScalarTypeSpec
    with the correct type patterns.
    """
    from bifrostrpc.typing import ScalarTypeSpec

    def _test(ts: Any) -> bool:
        return (
            isinstance(ts, ScalarTypeSpec)
            and ts.originalType is originalType
            and ts.scalarType is scalarType
            and ts.typeName == typeName
        )
    return _test


def ListTester(
    item_test: Callable[[Any], bool],
) -> Callable[[Any], bool]:
    """
    Return a callable that tests whether a given TypeSpec is a ListTypeSpec
    with the expected itemSpec.
    """
    from bifrostrpc.typing import ListTypeSpec

    def _test(ts: Any) -> bool:
        return isinstance(ts, ListTypeSpec) and item_test(ts.itemSpec)

    return _test


def DictTester(
    value_test: Callable[[Any], bool],
) -> Callable[[Any], bool]:
    """
    Return a callable that tests whether a given TypeSpec is a DictTypeSpec
    with the expected valueSpec.

    It is assumed that keySpec must be a ScalarTypeSpec[str], since that is the
    only type of Dict we support.
    """
    from bifrostrpc.typing import DictTypeSpec, ScalarTypeSpec

    def _test(ts: Any) -> bool:
        if not isinstance(ts, DictTypeSpec):
            return False

        assert isinstance(ts.keySpec, ScalarTypeSpec)
        assert ts.keySpec.scalarType is str
        assert ts.keySpec.originalType is str
        assert ts.keySpec.typeName == 'str'

        return value_test(ts.valueSpec)

    return _test


def _assert_union_variants(
    ts: Any,
    *expected: Callable[[Any], bool],
) -> None:
    from bifrostrpc.typing import UnionTypeSpec

    assert isinstance(ts, UnionTypeSpec)

    copy = list(expected)

    for variant in ts.variants:
        for idx, fn in enumerate(copy):
            if fn(variant):
                # we have matched this expected variant, remove it
                copy.pop(idx)
                break
        else:
            import pprint
            print('copy = ' + pprint.pformat(copy))  # noqa TODO
            raise Exception(
                f"UnionTypeSpec variant {variant!r} was not expected"
            )

    if len(copy):
        raise Exception(
                f"UnionTypeSpec did not contain a variant matching {copy[0]!r}"
        )


def test_get_Union_type_spec() -> None:
    from bifrostrpc.typing import Advanced
    from bifrostrpc.typing import getTypeSpec

    # test handling of a simple Union[str, int, None]
    _assert_union_variants(
        getTypeSpec(Union[str, int, None], Advanced()),
        is_null_spec,
        ScalarTester(str, str, 'str'),
        ScalarTester(int, int, 'int'),
    )

    # test handling of Optional[]
    _assert_union_variants(
        getTypeSpec(Optional[str], Advanced()),
        is_null_spec,
        ScalarTester(str, str, 'str'),
    )

    # test handling of nested Unions - note that nested unions are collapsed
    _assert_union_variants(
        getTypeSpec(Union[str, Union[int, None]], Advanced()),
        is_null_spec,
        ScalarTester(str, str, 'str'),
        ScalarTester(int, int, 'int'),
    )

    _assert_union_variants(
        getTypeSpec(Union[str, Optional[int]], Advanced()),
        is_null_spec,
        ScalarTester(str, str, 'str'),
        ScalarTester(int, int, 'int'),
    )

    # test Union containing more complex types: Union[List[], Dict[]]
    _assert_union_variants(
        getTypeSpec(Union[List[int], Dict[str, int]], Advanced()),
        ListTester(ScalarTester(int, int, 'int')),
        DictTester(ScalarTester(int, int, 'int')),
    )

    # test Union containing some NewTypes
    MyInt = NewType('MyInt', int)
    MyStr = NewType('MyStr', str)
    MyInt2 = NewType('MyInt2', MyInt)
    MyStr2 = NewType('MyStr2', MyStr)
    adv = Advanced()
    adv.addNewType(MyInt)
    adv.addNewType(MyStr)
    adv.addNewType(MyInt2)
    adv.addNewType(MyStr2)
    _assert_union_variants(
        getTypeSpec(Union[List[MyInt2], Dict[str, MyStr2]], adv),
        ListTester(ScalarTester(MyInt2, int, 'MyInt2')),
        DictTester(ScalarTester(MyStr2, str, 'MyStr2')),
    )


def test_get_Literal_type_spec() -> None:
    from bifrostrpc.typing import Advanced
    from bifrostrpc.typing import getTypeSpec
    from bifrostrpc.typing import LiteralTypeSpec

    Five = NewType('Five', Literal[5])
    Hello = NewType('Hello', Literal["hello"])
    adv = Advanced()
    adv.addNewType(Five)
    adv.addNewType(Hello)

    ts = getTypeSpec(Literal[5], adv)
    assert isinstance(ts, LiteralTypeSpec)
    assert ts.expected == 5
    assert ts.expectedType is int

    ts = getTypeSpec(Five, adv)
    assert isinstance(ts, LiteralTypeSpec)
    assert ts.expected == 5
    assert ts.expectedType is int

    ts = getTypeSpec(Hello, adv)
    assert isinstance(ts, LiteralTypeSpec)
    assert ts.expected == "hello"
    assert ts.expectedType is str
