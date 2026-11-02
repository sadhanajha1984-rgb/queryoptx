"""
Cardinality Estimator Module
Implements statistical selectivity estimation for filter predicates and join operations.
"""
import re
from typing import List, Optional
from app.parser.ast_models import ExpressionInternal, JoinInternal
from app.statistics.stats_models import DatabaseCatalog

class CardinalityEstimator:
    """
    Estimates selectivity and resulting tuple counts using database statistics.
    """

    @classmethod
    def estimate_filter_selectivity(cls, predicate: ExpressionInternal, catalog: DatabaseCatalog) -> float:
        """
        Calculates selectivity factor s in [0.0001, 1.0] for a single table predicate.
        """
        if predicate.is_join:
            return 1.0

        table_name = (predicate.table_affinity or "").lower()
        col_name = ""

        # Extract column name from left or raw expression
        col_match = re.search(r"(\w+)\.(\w+)", predicate.left)
        if col_match:
            table_name = col_match.group(1).lower()
            col_name = col_match.group(2).lower()
        else:
            col_match_single = re.search(r"\b([a-zA-Z_]\w*)\b", predicate.left)
            if col_match_single:
                col_name = col_match_single.group(1).lower()

        col_stat = catalog.get_column(table_name, col_name) if table_name else None
        n_distinct = col_stat.distinct_values if col_stat and col_stat.distinct_values > 0 else 10

        op = predicate.operator.strip().upper()

        if op in ("=", "=="):
            # Equality selectivity: 1 / N_distinct
            return max(0.0001, 1.0 / n_distinct)
        elif op in ("<>", "!="):
            # Inequality selectivity: 1 - 1 / N_distinct
            eq_sel = 1.0 / n_distinct
            return max(0.001, 1.0 - eq_sel)
        elif op in (">", ">=", "<", "<="):
            # Range predicate: Try range interpolation or standard 0.33
            if col_stat and col_stat.min_value and col_stat.max_value:
                try:
                    val = float(str(predicate.right).strip("'\""))
                    min_v = float(col_stat.min_value)
                    max_v = float(col_stat.max_value)
                    if max_v > min_v:
                        if op in (">", ">="):
                            sel = (max_v - val) / (max_v - min_v)
                        else:
                            sel = (val - min_v) / (max_v - min_v)
                        return max(0.01, min(0.99, sel))
                except Exception:
                    pass
            return 0.33
        elif op == "LIKE":
            return 0.10
        elif op == "IN":
            return min(0.5, max(0.05, 3.0 / n_distinct))
        else:
            return 0.25

    @classmethod
    def estimate_scan_cardinality(
        cls,
        table_name: str,
        predicates: List[ExpressionInternal],
        catalog: DatabaseCatalog
    ) -> float:
        """
        Estimates the output rows for scanning a base table after applying all pushed-down predicates.
        """
        tbl = catalog.get_table(table_name)
        if not tbl:
            return 1000.0  # default fallback

        total_rows = float(tbl.row_count)
        if not predicates:
            return total_rows

        # Combine independent predicate selectivities via product (conjunction)
        combined_selectivity = 1.0
        for p in predicates:
            s = cls.estimate_filter_selectivity(p, catalog)
            combined_selectivity *= s

        return max(1.0, total_rows * combined_selectivity)

    @classmethod
    def estimate_join_cardinality(
        cls,
        left_table: str,
        left_rows: float,
        right_table: str,
        right_rows: float,
        join_info: Optional[JoinInternal],
        catalog: DatabaseCatalog
    ) -> float:
        """
        Estimates the output rows of a join between two relations.
        Formula: (Rows_L * Rows_R) / max(V(Left, A), V(Right, B))
        """
        if not join_info:
            # Cartesian product / cross product if no join condition
            return max(1.0, left_rows * right_rows)

        col_l = catalog.get_column(join_info.left_table, join_info.left_column)
        col_r = catalog.get_column(join_info.right_table, join_info.right_column)

        dist_l = col_l.distinct_values if col_l and col_l.distinct_values > 0 else 10
        dist_r = col_r.distinct_values if col_r and col_r.distinct_values > 0 else 10

        denom = max(1.0, float(max(dist_l, dist_r)))
        est_rows = (left_rows * right_rows) / denom
        return max(1.0, est_rows)
