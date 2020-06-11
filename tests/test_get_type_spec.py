from typing import Dict, List, NewType

from pytest import raises  # type: ignore


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
