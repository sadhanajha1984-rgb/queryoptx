"""
Query Rewrite Rules & Provenance Models
"""
from dataclasses import dataclass, field
from typing import List

@dataclass
class RewriteProvenance:
    rule_name: str
    description: str
    before_summary: str
    after_summary: str
    nodes_affected: List[str] = field(default_factory=list)
