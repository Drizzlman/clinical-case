"""Domain errors. Framework-free: raised by entities and use cases."""


class DomainError(Exception):
    """Base class for domain-level errors."""


class DomainValidationError(DomainError):
    """An invariant of the domain was violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """A requested aggregate does not exist."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
