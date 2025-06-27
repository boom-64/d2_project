"""Custom errors."""


class PatternMismatchError(ValueError):
    """Custom exception for when string doesn't match pattern.

    Attributes:
        value (str): Value to match.
        pattern (str): Pattern to match.
        pattern_for (str): Short descriptor of pattern purpose.

    """

    def __init__(self, *, value: str, pattern: str, pattern_for: str) -> None:
        """Initialise class."""
        self.value: str = value
        self.pattern: str = pattern
        self.pattern_for: str = pattern_for
        super().__init__()
