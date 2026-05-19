from whooshql.infer.codec import detect_compression, detect_format
from whooshql.infer.delimiter import infer_delimiter
from whooshql.infer.header import has_header
from whooshql.infer.manifest import classify_manifest_key
from whooshql.infer.partition import detect_partition_values

__all__ = [
    "classify_manifest_key",
    "detect_compression",
    "detect_format",
    "detect_partition_values",
    "has_header",
    "infer_delimiter",
]
