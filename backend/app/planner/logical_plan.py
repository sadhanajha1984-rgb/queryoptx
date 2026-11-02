"""
Logical Query Plan Builder
Translates AST into canonical unoptimized Relational Algebra plan tree.
"""
from typing import List, Optional
from app.parser.ast_models import ParsedQueryInternal
from app.planner.tree_models import PlanNode
from app.statistics.cardinality_estimator import CardinalityEstimator
from app.statistics.stats_models import DatabaseCatalog

class LogicalPlanBuilder:
    """
    Constructs the canonical logical plan:
    Projection (Top)
      └─ OrderBy (Sort)
          └─ GroupBy (Aggregate)
              └─ Selection (Filter with all WHERE predicates combined)
                  └─ Joins (Left-deep tree of unoptimized logical joins)
                      └─ Scans (Base table scans)
    """

    @classmethod
    def build_canonical_plan(cls, parsed: ParsedQueryInternal, catalog: DatabaseCatalog) -> PlanNode:
        if not parsed.tables:
            return PlanNode(node_type="Scan", operator_name="EmptyScan", details={"info": "No tables"})

        # 1. Build Base Scans
        table_scan_nodes: List[PlanNode] = []
        for tbl in parsed.tables:
            t_name = tbl.name.lower()
            tbl_stat = catalog.get_table(t_name)
            rows = float(tbl_stat.row_count) if tbl_stat else 1000.0
            node = PlanNode(
                node_type="Scan",
                operator_name=f"LogicalScan ({tbl.identifier})",
                details={"table": t_name, "alias": tbl.alias, "columns": [c.name for c in (tbl_stat.columns.values() if tbl_stat else [])]},
                estimated_rows=rows
            )
            table_scan_nodes.append(node)

        # 2. Build Joins Tree (Canonical left-to-right)
        current_join_root = table_scan_nodes[0]
        for i in range(1, len(table_scan_nodes)):
            right_node = table_scan_nodes[i]
            # Find matching join condition if any
            left_tbls = [parsed.tables[k].identifier for k in range(i)]
            right_tbl = parsed.tables[i].identifier
            matching_join = None
            for j in parsed.joins:
                if (j.left_table in left_tbls and j.right_table == right_tbl) or \
                   (j.right_table in left_tbls and j.left_table == right_tbl):
                    matching_join = j
                    break

            join_cond_str = matching_join.raw_condition if matching_join else "True (Cross Join)"
            est_join_rows = CardinalityEstimator.estimate_join_cardinality(
                left_table=current_join_root.details.get("table", "left"),
                left_rows=current_join_root.estimated_rows,
                right_table=right_node.details.get("table", "right"),
                right_rows=right_node.estimated_rows,
                join_info=matching_join,
                catalog=catalog
            )

            join_node = PlanNode(
                node_type="Join",
                operator_name=f"LogicalJoin ({matching_join.join_type if matching_join else 'CROSS'})",
                details={"condition": join_cond_str, "type": matching_join.join_type if matching_join else "CROSS"},
                estimated_rows=est_join_rows,
                children=[current_join_root, right_node]
            )
            current_join_root = join_node

        # 3. Add Selection (Filter) node on top (Naive approach before rewrite)
        current_top = current_join_root
        if parsed.predicates:
            all_preds_str = " AND ".join([p.raw_sql for p in parsed.predicates])
            # Estimate combined selectivity
            combined_sel = 1.0
            for p in parsed.predicates:
                combined_sel *= CardinalityEstimator.estimate_filter_selectivity(p, catalog)

            filter_rows = max(1.0, current_top.estimated_rows * combined_sel)
            filter_node = PlanNode(
                node_type="Filter",
                operator_name="Selection (Filter)",
                details={"predicate": all_preds_str, "predicates_list": [p.raw_sql for p in parsed.predicates]},
                estimated_rows=filter_rows,
                children=[current_top]
            )
            current_top = filter_node

        # 4. Add Group By / Aggregate node if required
        if parsed.group_by or parsed.has_aggregates:
            agg_node = PlanNode(
                node_type="Aggregate",
                operator_name="LogicalAggregate",
                details={"group_by": parsed.group_by, "aggregates": [p.name for p in parsed.projections if "(" in p.name]},
                estimated_rows=max(1.0, current_top.estimated_rows * 0.5 if parsed.group_by else 1.0),
                children=[current_top]
            )
            current_top = agg_node

        # 5. Add Order By (Sort) node if required
        if parsed.order_by:
            sort_node = PlanNode(
                node_type="Sort",
                operator_name="LogicalSort",
                details={"order_by": parsed.order_by},
                estimated_rows=current_top.estimated_rows,
                children=[current_top]
            )
            current_top = sort_node

        # 6. Add Projection (Top)
        proj_node = PlanNode(
            node_type="Project",
            operator_name="LogicalProjection",
            details={"columns": [p.full_name() for p in parsed.projections]},
            estimated_rows=current_top.estimated_rows,
            children=[current_top]
        )

        return proj_node
