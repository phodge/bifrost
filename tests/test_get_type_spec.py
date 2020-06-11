from typing import NewType


def test_get_int_type_spec():
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


def test_get_str_type_spec():
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
