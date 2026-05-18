class WhooshError(Exception):
    """Base class for all user-facing whoosh exceptions."""


class FrameIOError(WhooshError):
    """Input/output read/write errors."""


class SchemaError(WhooshError):
    """Schema parsing, conversion, or validation errors."""


class DialectError(WhooshError):
    """CSV dialect parsing or detection errors."""


class CredentialError(WhooshError):
    """Credential resolution errors for object stores."""


class CompressionError(WhooshError):
    """Compression detection or decompression errors."""


class SliceSpecError(WhooshError):
    """Invalid row/column slice specification."""
