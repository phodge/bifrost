from typing import Literal, NewType, Optional, Type, Union

import pytest
from paradox.typing import CrossBool, CrossCustomType, CrossNum, CrossStr

from bifrostrpc.typing import (Advanced, LiteralTypeSpec, NullTypeSpec,
                               ScalarTypeSpec, UnionTypeSpec,
                               _getNewTypeBaseCrossType, getTypeSpec)


@pytest.mark.parametrize('scalarType', [int, str, bool])
def test_getTypeSpec_scalar(scalarType: Union[Type[int], Type[str], Type[bool]]) -> None:
    # first as just the scalar type
    spec1 = getTypeSpec(scalarType, adv=Advanced())
    assert isinstance(spec1, ScalarTypeSpec)
    assert spec1.scalarType is scalarType

    # then as Optional[T]
    spec2 = getTypeSpec(Optional[scalarType], adv=Advanced())
    assert isinstance(spec2, UnionTypeSpec)
    assert len(spec2.variants) == 2
    assert isinstance(spec2.variants[0], ScalarTypeSpec)
    assert isinstance(spec2.variants[1], NullTypeSpec)
    assert spec2.variants[0].scalarType is scalarType


def test_getTypeSpec_NewType() -> None:
    UserID = NewType('UserID', int)
    UserName = NewType('UserName', str)

    # first, verify that getTypeSpec() raises a TypeError for a NewType that isn't registered
    with pytest.raises(TypeError, match="Can't resolve"):
        getTypeSpec(UserID, adv=Advanced())

    adv = Advanced()
    adv.addNewType(UserID)
    adv.addNewType(UserName)

    spec1 = getTypeSpec(UserID, adv=adv)
    assert isinstance(spec1, ScalarTypeSpec)
    assert spec1.scalarType is int
    assert spec1.originalType is UserID
    assert spec1.typeName == 'UserID'

    spec2 = getTypeSpec(UserName, adv=adv)
    assert isinstance(spec2, ScalarTypeSpec)
    assert spec2.scalarType is str
    assert spec2.originalType is UserName
    assert spec2.typeName == 'UserName'


def test_getTypeSpec_union() -> None:
    # first a normal union
    spec1 = getTypeSpec(Union[int, str, bool], adv=Advanced())
    assert isinstance(spec1, UnionTypeSpec)
    assert len(spec1.variants) == 3
    assert isinstance(spec1.variants[0], ScalarTypeSpec)
    assert isinstance(spec1.variants[1], ScalarTypeSpec)
    assert isinstance(spec1.variants[2], ScalarTypeSpec)
    assert spec1.variants[0].scalarType is int
    assert spec1.variants[1].scalarType is str
    assert spec1.variants[2].scalarType is bool

    # then an Optional union - this will actually just add NullTypeSpec to the end of the Union
    spec2 = getTypeSpec(Optional[Union[int, str, bool]], adv=Advanced())
    assert isinstance(spec2, UnionTypeSpec)
    assert len(spec2.variants) == 4
    assert isinstance(spec2.variants[0], ScalarTypeSpec)
    assert isinstance(spec2.variants[1], ScalarTypeSpec)
    assert isinstance(spec2.variants[2], ScalarTypeSpec)
    assert isinstance(spec2.variants[3], NullTypeSpec)
    assert spec2.variants[0].scalarType is int
    assert spec2.variants[1].scalarType is str
    assert spec2.variants[2].scalarType is bool

    # should be able to construct something similar with Union[None, int]
    spec3 = getTypeSpec(Union[None, int, str], adv=Advanced())
    assert isinstance(spec3, UnionTypeSpec)
    assert len(spec3.variants) == 3
    assert isinstance(spec3.variants[0], NullTypeSpec)
    assert isinstance(spec3.variants[1], ScalarTypeSpec)
    assert isinstance(spec3.variants[2], ScalarTypeSpec)
    assert spec3.variants[1].scalarType is int
    assert spec3.variants[2].scalarType is str

    # Optional[Union[None...]]]:
    # This shouldn't add an extra NullTypeSpec to the Union, however this is
    # accomplished by Optional[...] recognising that its inner type is
    # Union[None, ...], not by bifrost
    spec4 = getTypeSpec(Optional[Union[None, int, str]], adv=Advanced())
    assert isinstance(spec4, UnionTypeSpec)
    assert len(spec4.variants) == 3
    assert isinstance(spec4.variants[0], NullTypeSpec)
    assert isinstance(spec4.variants[1], ScalarTypeSpec)
    assert isinstance(spec4.variants[2], ScalarTypeSpec)
    assert spec4.variants[1].scalarType is int
    assert spec4.variants[2].scalarType is str


def test_getTypeSpec_literal() -> None:
    # TODO: add support multiple Literal values
    spec1 = getTypeSpec(Literal[5], adv=Advanced())
    assert isinstance(spec1, LiteralTypeSpec)
    assert spec1.expected == 5
    assert spec1.expectedType is int


def test_getNewTypeBaseCrossType() -> None:
    UserID = NewType('UserID', int)
    AdminID = NewType('AdminID', UserID)

    assert isinstance(_getNewTypeBaseCrossType(NewType('UserName', str)), CrossStr)
    assert isinstance(_getNewTypeBaseCrossType(UserID), CrossNum)
    assert isinstance(_getNewTypeBaseCrossType(NewType('UserActive', bool)), CrossBool)
    assert isinstance(_getNewTypeBaseCrossType(AdminID), CrossCustomType)

    # TODO: add tests/support for non-scalar NewTypes
