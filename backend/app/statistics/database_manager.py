"""
Multi-Database Manager for QueryOptX.
Supports both built-in demonstration databases and custom user-created databases.
Each database has its own SQLite execution instance and dynamic statistics catalog.
"""
import os
import re
import sqlite3
import time
from typing import Dict, List, Optional, Tuple, Any

from app.statistics.mock_catalog import build_default_catalog
from app.statistics.stats_models import ColumnStatistics, DatabaseCatalog, TableStatistics

class DatabaseInstance:
    def __init__(self, db_id: str, name: str, description: str, is_custom: bool = True):
        self.db_id = db_id
        self.name = name
        self.description = description
        self.is_custom = is_custom
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.catalog = DatabaseCatalog()
        self.created_at = time.time()
        self.schema_ddl: str = ""

    def execute_ddl(self, ddl_statements: str) -> Tuple[bool, str, int]:
        """
        Executes user DDL/DML statements (CREATE TABLE, CREATE INDEX, INSERT)
        and regenerates database statistics catalog.
        """
        cur = self.conn.cursor()
        stmts = [s.strip() for s in ddl_statements.split(";") if s.strip()]
        executed = 0
        try:
            for s in stmts:
                # Disallow system calls or dangerous PRAGMAs if needed, but allow DDL/INSERT
                cur.execute(s)
                executed += 1
            self.conn.commit()
            if self.schema_ddl:
                self.schema_ddl += ("\n\n" + ddl_statements.strip())
            else:
                self.schema_ddl = ddl_statements.strip()
            self.refresh_catalog()
            return True, f"Successfully executed {executed} statements.", executed
        except Exception as e:
            self.conn.rollback()
            return False, str(e), executed

    def reset_and_reload(self, ddl_statements: str) -> Tuple[bool, str, int]:
        """
        Completely resets SQLite in-memory instance and executes new schema/data script.
        Used for editing the database schema and adding/modifying tables cleanly.
        """
        new_conn = sqlite3.connect(":memory:", check_same_thread=False)
        cur = new_conn.cursor()
        stmts = [s.strip() for s in ddl_statements.split(";") if s.strip()]
        executed = 0
        try:
            for s in stmts:
                cur.execute(s)
                executed += 1
            new_conn.commit()
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = new_conn
            self.schema_ddl = ddl_statements.strip()
            self.refresh_catalog()
            return True, f"Database reset and successfully executed {executed} statements.", executed
        except Exception as e:
            new_conn.rollback()
            try:
                new_conn.close()
            except Exception:
                pass
            return False, str(e), executed

    def refresh_catalog(self):
        """
        Introspects tables, rows, columns, and indexes from sqlite_master
        and statistical pragma commands.
        """
        new_catalog = DatabaseCatalog()
        cur = self.conn.cursor()
        
        # Get tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cur.fetchall()]

        for tbl_name in tables:
            tname = tbl_name.lower()
            try:
                cur.execute(f"SELECT COUNT(*) FROM \"{tbl_name}\";")
                row_cnt = cur.fetchone()[0]
            except Exception:
                row_cnt = 0
            
            # Estimate pages (approx 100 bytes/row, 8192 bytes/page)
            page_cnt = max(1, (max(1, row_cnt) * 100) // 8192 + 1)
            
            tbl_stat = TableStatistics(
                name=tname,
                row_count=row_cnt,
                page_count=page_cnt,
                avg_row_width=100,
                columns={},
                indexes=[]
            )

            # Get columns
            cur.execute(f"PRAGMA table_info(\"{tbl_name}\");")
            cols_info = cur.fetchall()
            for col in cols_info:
                cid, cname, ctype, notnull, dflt_value, pk = col
                col_name_lower = cname.lower()
                
                # Count distinct
                distinct_val = 1
                null_fraction = 0.0
                min_v = None
                max_v = None
                if row_cnt > 0:
                    try:
                        cur.execute(f"SELECT COUNT(DISTINCT \"{cname}\"), COUNT(*) - COUNT(\"{cname}\"), MIN(\"{cname}\"), MAX(\"{cname}\") FROM \"{tbl_name}\";")
                        row = cur.fetchone()
                        if row:
                            distinct_val = max(1, row[0])
                            null_count = row[1]
                            null_fraction = float(null_count) / float(row_cnt)
                            min_v = str(row[2]) if row[2] is not None else None
                            max_v = str(row[3]) if row[3] is not None else None
                    except Exception:
                        distinct_val = max(1, row_cnt // 2)

                tbl_stat.columns[col_name_lower] = ColumnStatistics(
                    name=col_name_lower,
                    data_type=ctype.lower() if ctype else "text",
                    distinct_values=distinct_val,
                    null_fraction=null_fraction,
                    min_value=min_v,
                    max_value=max_v,
                    has_index=bool(pk),
                    index_name=f"pk_{tname}_{col_name_lower}" if pk else None
                )

            # Get indexes
            cur.execute(f"PRAGMA index_list(\"{tbl_name}\");")
            idx_list = cur.fetchall()
            for idx in idx_list:
                idx_name = idx[1]
                tbl_stat.indexes.append(idx_name)
                cur.execute(f"PRAGMA index_info(\"{idx_name}\");")
                idx_cols = cur.fetchall()
                for icol in idx_cols:
                    col_name = icol[2].lower()
                    if col_name in tbl_stat.columns:
                        tbl_stat.columns[col_name].has_index = True
                        tbl_stat.columns[col_name].index_name = idx_name

            new_catalog.tables[tname] = tbl_stat

        self.catalog = new_catalog


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None

    def __init__(self):
        self.databases: Dict[str, DatabaseInstance] = {}
        self.active_db_id: str = "default_univ"
        self._init_default_databases()

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def _init_default_databases(self):
        # 1. Default University & E-Commerce DB
        default_db = DatabaseInstance(
            db_id="default_univ",
            name="University & Retail Benchmark DB (Predefined)",
            description="Preloaded university academics (students, courses, enrollments) and e-commerce retail benchmark schema.",
            is_custom=False
        )
        # Populate using seed sql simulation
        from app.execution.executor import QueryExecutor
        # Get schema from QueryExecutor
        sqlite_init = QueryExecutor._get_sqlite_db()
        # Transfer data or initialize directly
        cur_src = sqlite_init.cursor()
        cur_dest = default_db.conn.cursor()
        
        # Dump from template connection
        for line in sqlite_init.iterdump():
            if not line.startswith("BEGIN") and not line.startswith("COMMIT"):
                try:
                    cur_dest.execute(line)
                except Exception:
                    pass
        default_db.conn.commit()
        default_db.catalog = build_default_catalog(scale=10000)
        default_db.refresh_catalog()
        # Overlay mock catalog table stats for richer demonstration if tables match
        built_catalog = build_default_catalog(scale=10000)
        for tname, stat in built_catalog.tables.items():
            if tname in default_db.catalog.tables:
                # keep actual indexes and columns, update scale counts for demonstration
                default_db.catalog.tables[tname].row_count = max(default_db.catalog.tables[tname].row_count, stat.row_count)
                default_db.catalog.tables[tname].page_count = max(default_db.catalog.tables[tname].page_count, stat.page_count)
                for cname, cstat in stat.columns.items():
                    if cname in default_db.catalog.tables[tname].columns:
                        default_db.catalog.tables[tname].columns[cname].has_index = cstat.has_index
                        default_db.catalog.tables[tname].columns[cname].index_name = cstat.index_name

        self.databases["default_univ"] = default_db

    def get_active_db(self) -> DatabaseInstance:
        if self.active_db_id not in self.databases:
            self.active_db_id = "default_univ"
        return self.databases[self.active_db_id]

    def set_active_db(self, db_id: str) -> bool:
        if db_id in self.databases:
            self.active_db_id = db_id
            return True
        return False

    def create_database(self, name: str, description: str, ddl: Optional[str] = None) -> DatabaseInstance:
        db_id = "user_db_" + re.sub(r"[^a-zA-Z0-9_]", "_", name.lower()).strip("_")
        if not db_id or db_id == "user_db_":
            db_id = f"user_db_{int(time.time())}"
        
        # Avoid duplicate collision
        base_id = db_id
        counter = 1
        while db_id in self.databases:
            db_id = f"{base_id}_{counter}"
            counter += 1

        new_db = DatabaseInstance(
            db_id=db_id,
            name=name,
            description=description,
            is_custom=True
        )
        if ddl and ddl.strip():
            new_db.execute_ddl(ddl)
        
        self.databases[db_id] = new_db
        self.active_db_id = db_id
        return new_db

    def delete_database(self, db_id: str) -> bool:
        if db_id == "default_univ":
            return False  # Protected
        if db_id in self.databases:
            del self.databases[db_id]
            if self.active_db_id == db_id:
                self.active_db_id = "default_univ"
            return True
        return False

    def list_databases(self) -> List[Dict[str, Any]]:
        result = []
        for db in self.databases.values():
            result.append({
                "db_id": db.db_id,
                "name": db.name,
                "description": db.description,
                "is_custom": db.is_custom,
                "is_active": db.db_id == self.active_db_id,
                "table_count": len(db.catalog.tables),
                "tables": list(db.catalog.tables.keys()),
                "schema_ddl": db.schema_ddl
            })
        return result

