class WhooshQLError(Exception):
    """Base class for all user-facing whooshql exceptions."""


class FrameIOError(WhooshQLError):
    """Input/output read/write errors."""


class SchemaError(WhooshQLError):
    """Schema parsing, conversion, or validation errors."""


class DialectError(WhooshQLError):
    """CSV dialect parsing or detection errors."""


class CredentialError(WhooshQLError):
    """Credential resolution errors for object stores."""


class CompressionError(WhooshQLError):
    """Compression detection or decompression errors."""


class SliceSpecError(WhooshQLError):
    """Invalid row/column slice specification."""
