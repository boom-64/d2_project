from typing import Tuple
def ensure_type(
    *,
    name: str, 
    val: object, 
    types: type | Tuple[type, ...]
) -> None:
    if not isinstance(val, types):
        expected_names = (
            types.__name__
            if isinstance(types, type)
            else ", ".join(t.__name__ for t in types)
        )
        raise TypeError(
            f"'{name}' must be of type {expected_names}, "
            f"got {type(val).__name__} instead (value: {val!r})."
        )
