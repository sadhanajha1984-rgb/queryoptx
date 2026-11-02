"""
SQL Parser Module using sqlglot
Converts SQL SELECT queries into normalized ParsedQueryInternal AST representations.
"""
from typing import Any, Dict, List, Optional, Tuple
import sqlglot
from sqlglot import exp

from app.parser.ast_models import (
    ColumnRef,
    ExpressionInternal,
    JoinInternal,
    ParsedQueryInternal,
    TableRefInternal
)
from app.parser.validator import validate_sql_safety

class SQLParser:
    """
    Parses SQL SELECT queries into normalized intermediate representations.
    """

    @classmethod
    def parse(cls, sql: str) -> ParsedQueryInternal:
        is_safe, error_msg = validate_sql_safety(sql)
        if not is_safe:
            raise ValueError(f"SQL validation error: {error_msg}")

        try:
            parsed = sqlglot.parse_one(sql, read="postgres")
        except Exception as e:
            raise ValueError(f"Syntax error in SQL: {str(e)}")

        if not isinstance(parsed, exp.Select):
            raise ValueError("Query must be a valid SELECT statement.")

        tables: List[TableRefInternal] = []
        table_aliases: Dict[str, str] = {}  # alias/identifier -> real table name

        # 1. Extract all Tables (FROM & JOINs)
        for tbl_expr in parsed.find_all(exp.Table):
            tbl_name = tbl_expr.name
            alias = tbl_expr.alias if tbl_expr.alias else None
            if not any(t.name == tbl_name and t.alias == alias for t in tables):
                tables.append(TableRefInternal(name=tbl_name, alias=alias))
                table_aliases[alias if alias else tbl_name] = tbl_name
                table_aliases[tbl_name] = tbl_name

        # 2. Extract JOINs
        joins: List[JoinInternal] = []
        for j in parsed.find_all(exp.Join):
            on_condition = j.args.get("on")
            join_kind = j.args.get("kind", "INNER") or "INNER"
            if on_condition:
                cls._extract_join_conditions(on_condition, joins, join_kind, table_aliases)

        # 3. Extract Projections
        projections: List[ColumnRef] = []
        has_aggregates = False
        select_expressions = parsed.expressions
        for expr in select_expressions:
            if isinstance(expr, exp.Star):
                projections.append(ColumnRef(table=None, name="*", alias=None))
            elif isinstance(expr, exp.Column):
                table_prefix = expr.table if expr.table else None
                real_table = table_aliases.get(table_prefix, table_prefix)
                projections.append(ColumnRef(table=real_table, name=expr.name, alias=expr.alias))
            elif isinstance(expr, exp.Anonymous) or isinstance(expr, exp.Func):
                has_aggregates = True
                alias = expr.alias if expr.alias else expr.sql()
                projections.append(ColumnRef(table=None, name=expr.sql(), alias=alias))
            elif isinstance(expr, exp.Alias):
                child = expr.this
                if isinstance(child, (exp.Anonymous, exp.Func, exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
                    has_aggregates = True
                if isinstance(child, exp.Column):
                    tbl = table_aliases.get(child.table, child.table)
                    projections.append(ColumnRef(table=tbl, name=child.name, alias=expr.alias))
                else:
                    projections.append(ColumnRef(table=None, name=child.sql(), alias=expr.alias))
            else:
                projections.append(ColumnRef(table=None, name=expr.sql(), alias=None))

        # Check for aggregates in select
        for expr in parsed.find_all(exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max):
            has_aggregates = True

        # 4. Extract WHERE Predicates
        predicates: List[ExpressionInternal] = []
        where_clause = parsed.args.get("where")
        if where_clause and where_clause.this:
            cls._extract_where_predicates(where_clause.this, predicates, joins, table_aliases)

        # 5. Extract GROUP BY
        group_by: List[str] = []
        group = parsed.args.get("group")
        if group:
            for g in group.expressions:
                group_by.append(g.sql())

        # 6. Extract ORDER BY
        order_by: List[str] = []
        order = parsed.args.get("order")
        if order:
            for o in order.expressions:
                order_by.append(o.sql())

        # 7. Extract LIMIT
        limit_val = None
        limit = parsed.args.get("limit")
        if limit and limit.expression:
            try:
                limit_val = int(limit.expression.sql())
            except Exception:
                pass

        ast_dict = {
            "type": "Select",
            "tables": [{"name": t.name, "alias": t.alias} for t in tables],
            "projections": [p.name for p in projections],
            "joins_count": len(joins),
            "predicates_count": len(predicates)
        }

        return ParsedQueryInternal(
            raw_sql=sql,
            tables=tables,
            projections=projections,
            predicates=predicates,
            joins=joins,
            group_by=group_by,
            order_by=order_by,
            limit=limit_val,
            has_aggregates=has_aggregates,
            ast_dict=ast_dict
        )

    @classmethod
    def _extract_join_conditions(
        cls,
        condition_node: exp.Expression,
        joins: List[JoinInternal],
        join_type: str,
        table_aliases: Dict[str, str]
    ):
        if isinstance(condition_node, exp.And):
            cls._extract_join_conditions(condition_node.left, joins, join_type, table_aliases)
            cls._extract_join_conditions(condition_node.right, joins, join_type, table_aliases)
        elif isinstance(condition_node, exp.EQ):
            left = condition_node.left
            right = condition_node.right
            if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                left_tbl = table_aliases.get(left.table, left.table or "unknown")
                right_tbl = table_aliases.get(right.table, right.table or "unknown")
                joins.append(
                    JoinInternal(
                        left_table=left_tbl,
                        right_table=right_tbl,
                        left_column=left.name,
                        right_column=right.name,
                        join_type=join_type.upper(),
                        raw_condition=condition_node.sql()
                    )
                )

    @classmethod
    def _extract_where_predicates(
        cls,
        node: exp.Expression,
        predicates: List[ExpressionInternal],
        joins: List[JoinInternal],
        table_aliases: Dict[str, str]
    ):
        if isinstance(node, exp.And):
            cls._extract_where_predicates(node.left, predicates, joins, table_aliases)
            cls._extract_where_predicates(node.right, predicates, joins, table_aliases)
            return

        # Check if this WHERE clause is an implicit join (e.g. s.id = e.student_id)
        if isinstance(node, exp.EQ):
            left = node.left
            right = node.right
            if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                left_tbl = table_aliases.get(left.table, left.table or "unknown")
                right_tbl = table_aliases.get(right.table, right.table or "unknown")
                if left_tbl != right_tbl:
                    joins.append(
                        JoinInternal(
                            left_table=left_tbl,
                            right_table=right_tbl,
                            left_column=left.name,
                            right_column=right.name,
                            join_type="INNER",
                            raw_condition=node.sql()
                        )
                    )
                    return

        # Single table filter predicate
        tbl_affinity = None
        for col in node.find_all(exp.Column):
            if col.table:
                tbl_affinity = table_aliases.get(col.table, col.table)
                break

        op_name = node.key.upper() if hasattr(node, "key") else "="
        if isinstance(node, exp.EQ):
            op_name = "="
        elif isinstance(node, exp.NEQ):
            op_name = "<>"
        elif isinstance(node, exp.GT):
            op_name = ">"
        elif isinstance(node, exp.GTE):
            op_name = ">="
        elif isinstance(node, exp.LT):
            op_name = "<"
        elif isinstance(node, exp.LTE):
            op_name = "<="
        elif isinstance(node, exp.Like):
            op_name = "LIKE"
        elif isinstance(node, exp.In):
            op_name = "IN"

        left_repr = node.left.sql() if hasattr(node, "left") else node.sql()
        right_repr = node.right.sql() if hasattr(node, "right") else ""

        predicates.append(
            ExpressionInternal(
                left=left_repr,
                operator=op_name,
                right=right_repr,
                raw_sql=node.sql(),
                is_join=False,
                table_affinity=tbl_affinity
            )
        )
