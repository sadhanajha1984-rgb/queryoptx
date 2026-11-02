"""
Database Statistics Models
Represents relational metadata, page counts, distinct values, null fraction, and indexes.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ColumnStatistics:
    name: str
    data_type: str
    distinct_values: int
    null_fraction: float = 0.0
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    has_index: bool = False
    index_name: Optional[str] = None
    index_type: Optional[str] = "BTREE"

@dataclass
class TableStatistics:
    name: str
    row_count: int
    page_count: int
    avg_row_width: int
    columns: Dict[str, ColumnStatistics] = field(default_factory=dict)
    indexes: List[str] = field(default_factory=list)

@dataclass
class DatabaseCatalog:
    tables: Dict[str, TableStatistics] = field(default_factory=dict)

    def get_table(self, table_name: str) -> Optional[TableStatistics]:
        tbl = table_name.lower()
        return self.tables.get(tbl)

    def get_column(self, table_name: str, column_name: str) -> Optional[ColumnStatistics]:
        tbl = self.get_table(table_name)
        if tbl:
            return tbl.columns.get(column_name.lower())
        return None
