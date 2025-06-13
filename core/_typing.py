from typing import Tuple
def ensure_type(
    *,
    name: str, 
    val: object, 
    expected_types: type | Tuple[type, ...]
) -> None:
    if not isinstance(val, expected_types):
        expected_names = (
            expected_types.__name__
            if isinstance(expected_types, type)
            else ", ".join(t.__name__ for t in expected_types)
        )
        raise TypeError(
            f"'{name}' must be of type {expected_names}, "
            f"got {type(val).__name__} instead (value: {val!r})."
        )
