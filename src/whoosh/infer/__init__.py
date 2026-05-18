from whoosh.infer.codec import detect_compression, detect_format
from whoosh.infer.delimiter import infer_delimiter
from whoosh.infer.header import has_header
from whoosh.infer.manifest import classify_manifest_key
from whoosh.infer.partition import detect_partition_values

__all__ = [
    "classify_manifest_key",
    "detect_compression",
    "detect_format",
    "detect_partition_values",
    "has_header",
    "infer_delimiter",
]
