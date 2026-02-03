from enum import Enum


class RefType(str, Enum):
    CITATION = "citation"
    DELEGATION = "delegation"
    RANGE = "range"
    ADMIN_RULE = "admin_rule"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"

