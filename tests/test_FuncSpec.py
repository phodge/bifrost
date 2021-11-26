from pytest import raises  # type: ignore


def test_FuncSpec_typing_Any():
    from bifrostrpc.typing import Advanced, FuncSpec
    from bifrostrpc import TypeNotSupportedError
    from typing import Any

    def return_any() -> Any: return None
    def accept_any(a: Any) -> None: return None

    # "Any" return type is not allowed
    with raises(TypeNotSupportedError):
        FuncSpec(return_any, Advanced())

    # "Any" argument type is not allowed
    with raises(TypeNotSupportedError):
        FuncSpec(accept_any, Advanced())


def test_FuncSpec_scalar():
    from bifrostrpc.typing import Advanced, FuncSpec, ScalarTypeSpec
    from typing import Union

    def scalar_fn(i: int, s: str, b: bool) -> None:
        return None

    # "Any" return type is not allowed
    spec = FuncSpec(scalar_fn, Advanced())
    assert isinstance(spec.argSpecs['i'], ScalarTypeSpec)
    assert isinstance(spec.argSpecs['s'], ScalarTypeSpec)
    assert isinstance(spec.argSpecs['b'], ScalarTypeSpec)


def test_FuncSpec_typing_List():
    from bifrostrpc.typing import Advanced, FuncSpec
    from bifrostrpc import TypeNotSupportedError
    from typing import List

    def accept_list(things: List[int]) -> None: return None
    def return_list() -> List[int]: return []
    def list_of_lists(things: List[List[List[int]]]) -> List[List[List[str]]]: return []

    # "Any" return type is not allowed
    FuncSpec(accept_list, Advanced())
    FuncSpec(return_list, Advanced())
    FuncSpec(list_of_lists, Advanced())
