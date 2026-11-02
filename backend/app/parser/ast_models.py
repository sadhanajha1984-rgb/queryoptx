"""
AST Model definitions for normalized internal SQL representation
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class ColumnRef:
    table: Optional[str]
    name: str
    alias: Optional[str] = None

    def full_name(self) -> str:
        return f"{self.table}.{self.name}" if self.table else self.name

@dataclass
class TableRefInternal:
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None

    @property
    def identifier(self) -> str:
        return self.alias if self.alias else self.name

@dataclass
class ExpressionInternal:
    left: Any
    operator: str
    right: Any
    raw_sql: str
    is_join: bool = False
    table_affinity: Optional[str] = None

@dataclass
class JoinInternal:
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    join_type: str = "INNER"
    raw_condition: str = ""

@dataclass
class ParsedQueryInternal:
    raw_sql: str
    tables: List[TableRefInternal] = field(default_factory=list)
    projections: List[ColumnRef] = field(default_factory=list)
    predicates: List[ExpressionInternal] = field(default_factory=list)
    joins: List[JoinInternal] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    order_by: List[str] = field(default_factory=list)
    limit: Optional[int] = None
    has_aggregates: bool = False
    ast_dict: Dict[str, Any] = field(default_factory=dict)
