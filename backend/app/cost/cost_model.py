"""
Cost Model Module for QueryOptX
Implements modular formulas for I/O, CPU, and Memory costing across scans, joins, and materializations.
"""
import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from app.config import settings
from app.statistics.stats_models import ColumnStatistics, DatabaseCatalog, TableStatistics

@dataclass
class CostBreakdown:
    io_cost: float
    cpu_cost: float
    memory_cost: float
    total_cost: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "io_cost": round(self.io_cost, 4),
            "cpu_cost": round(self.cpu_cost, 4),
            "memory_cost": round(self.memory_cost, 4),
            "total_cost": round(self.total_cost, 4)
        }

class CostModel:
    """
    Modular database execution cost estimator.
    """

    def __init__(
        self,
        seq_page_cost: float = settings.SEQ_PAGE_COST,
        random_page_cost: float = settings.RANDOM_PAGE_COST,
        cpu_tuple_cost: float = settings.CPU_TUPLE_COST,
        cpu_index_tuple_cost: float = settings.CPU_INDEX_TUPLE_COST,
        cpu_operator_cost: float = settings.CPU_OPERATOR_COST,
        memory_page_cost: float = settings.MEMORY_PAGE_COST
    ):
        self.seq_page_cost = seq_page_cost
        self.random_page_cost = random_page_cost
        self.cpu_tuple_cost = cpu_tuple_cost
        self.cpu_index_tuple_cost = cpu_index_tuple_cost
        self.cpu_operator_cost = cpu_operator_cost
        self.memory_page_cost = memory_page_cost

    # ==========================================================
    # 1. Base Table Access Path Costing
    # ==========================================================

    def cost_seq_scan(
        self,
        table_stat: TableStatistics,
        filter_selectivity: float = 1.0
    ) -> CostBreakdown:
        """
        Sequential Scan Cost:
        I/O: Pages * seq_page_cost
        CPU: Rows * cpu_tuple_cost + Rows * cpu_operator_cost (filter eval)
        """
        io = float(table_stat.page_count) * self.seq_page_cost
        cpu = (float(table_stat.row_count) * self.cpu_tuple_cost) + (float(table_stat.row_count) * self.cpu_operator_cost)
        mem = 0.0
        return CostBreakdown(io_cost=io, cpu_cost=cpu, memory_cost=mem, total_cost=io + cpu + mem)

    def cost_index_scan(
        self,
        table_stat: TableStatistics,
        filter_selectivity: float,
        index_col: Optional[ColumnStatistics] = None
    ) -> CostBreakdown:
        """
        Index Scan Cost:
        I/O: B-Tree tree traversal (log2(Pages)) + estimated leaf pages fetched (selectivity * IndexPages)
             plus matching table heap pages (selectivity * Rows * random_page_cost)
        CPU: Filtered index tuples * cpu_index_tuple_cost + Fetched table tuples * cpu_tuple_cost
        """
        sel = max(0.0001, min(1.0, filter_selectivity))
        idx_pages = max(1.0, float(table_stat.page_count) * 0.2)  # Index is ~20% size of table
        b_tree_depth = max(1.0, math.log2(max(2.0, idx_pages)))

        io = (b_tree_depth * self.random_page_cost) + \
             (sel * idx_pages * self.random_page_cost) + \
             (sel * float(table_stat.row_count) * self.random_page_cost * 0.5)

        cpu = (sel * float(table_stat.row_count) * self.cpu_index_tuple_cost) + \
              (sel * float(table_stat.row_count) * self.cpu_tuple_cost)
        mem = 0.0
        return CostBreakdown(io_cost=io, cpu_cost=cpu, memory_cost=mem, total_cost=io + cpu + mem)

    def find_best_access_path(
        self,
        table_stat: TableStatistics,
        filter_selectivity: float,
        predicate_columns: list[str]
    ) -> Tuple[str, CostBreakdown]:
        """
        Evaluates SeqScan vs IndexScan and returns the cheapest access method and its cost.
        """
        seq_cost = self.cost_seq_scan(table_stat, filter_selectivity)

        # Check if an index is available on any predicate column
        has_usable_index = False
        for col_name in predicate_columns:
            col_stat = table_stat.columns.get(col_name.lower())
            if col_stat and col_stat.has_index:
                has_usable_index = True
                break

        if has_usable_index and filter_selectivity < 0.35:
            idx_cost = self.cost_index_scan(table_stat, filter_selectivity)
            if idx_cost.total_cost < seq_cost.total_cost:
                return "IndexScan", idx_cost

        return "SeqScan", seq_cost

    # ==========================================================
    # 2. Join Algorithm Costing
    # ==========================================================

    def cost_nested_loop_join(
        self,
        left_cost: CostBreakdown,
        left_rows: float,
        right_cost: CostBreakdown,
        right_rows: float
    ) -> CostBreakdown:
        """
        Nested Loop Join:
        Evaluates inner relation for each outer tuple.
        CPU: left_rows * right_rows * cpu_operator_cost
        """
        io = left_cost.io_cost + (left_rows * right_cost.io_cost * 0.1)  # cache buffer factor
        cpu = left_cost.cpu_cost + (left_rows * right_cost.cpu_cost) + (left_rows * right_rows * self.cpu_operator_cost)
        mem = left_cost.memory_cost + right_cost.memory_cost
        return CostBreakdown(io_cost=io, cpu_cost=cpu, memory_cost=mem, total_cost=io + cpu + mem)

    def cost_hash_join(
        self,
        left_cost: CostBreakdown,
        left_rows: float,
        right_cost: CostBreakdown,
        right_rows: float
    ) -> CostBreakdown:
        """
        Hash Join:
        Builds in-memory hash table on smaller relation (build input) and probes with larger relation.
        I/O: Left I/O + Right I/O
        CPU: left_rows * cpu_hash_build + right_rows * cpu_hash_probe
        Memory: build_pages * memory_page_cost
        """
        build_rows = min(left_rows, right_rows)
        probe_rows = max(left_rows, right_rows)

        build_pages = max(1.0, (build_rows * 80.0) / 8192.0)
        mem = (left_cost.memory_cost + right_cost.memory_cost) + (build_pages * self.memory_page_cost)

        io = left_cost.io_cost + right_cost.io_cost
        cpu = left_cost.cpu_cost + right_cost.cpu_cost + \
              (build_rows * self.cpu_operator_cost * 2.0) + \
              (probe_rows * self.cpu_operator_cost * 1.5)

        return CostBreakdown(io_cost=io, cpu_cost=cpu, memory_cost=mem, total_cost=io + cpu + mem)

    def cost_merge_join(
        self,
        left_cost: CostBreakdown,
        left_rows: float,
        right_cost: CostBreakdown,
        right_rows: float,
        left_sorted: bool = False,
        right_sorted: bool = False
    ) -> CostBreakdown:
        """
        Sort-Merge Join:
        Sorts inputs if not already sorted, then linear merge pass.
        """
        sort_left_cpu = 0.0 if left_sorted else (left_rows * math.log2(max(2.0, left_rows)) * self.cpu_operator_cost * 2.0)
        sort_right_cpu = 0.0 if right_sorted else (right_rows * math.log2(max(2.0, right_rows)) * self.cpu_operator_cost * 2.0)

        io = left_cost.io_cost + right_cost.io_cost
        cpu = left_cost.cpu_cost + right_cost.cpu_cost + sort_left_cpu + sort_right_cpu + \
              ((left_rows + right_rows) * self.cpu_operator_cost)
        mem = left_cost.memory_cost + right_cost.memory_cost
        return CostBreakdown(io_cost=io, cpu_cost=cpu, memory_cost=mem, total_cost=io + cpu + mem)

    # ==========================================================
    # 3. Post-Processing Operators (Sort, Aggregation, Projection)
    # ==========================================================

    def cost_sort(self, input_cost: CostBreakdown, input_rows: float) -> CostBreakdown:
        cpu = input_cost.cpu_cost + (input_rows * math.log2(max(2.0, input_rows)) * self.cpu_operator_cost * 2.0)
        return CostBreakdown(io_cost=input_cost.io_cost, cpu_cost=cpu, memory_cost=input_cost.memory_cost, total_cost=input_cost.io_cost + cpu + input_cost.memory_cost)

    def cost_aggregate(self, input_cost: CostBreakdown, input_rows: float) -> CostBreakdown:
        cpu = input_cost.cpu_cost + (input_rows * self.cpu_operator_cost)
        return CostBreakdown(io_cost=input_cost.io_cost, cpu_cost=cpu, memory_cost=input_cost.memory_cost, total_cost=input_cost.io_cost + cpu + input_cost.memory_cost)
