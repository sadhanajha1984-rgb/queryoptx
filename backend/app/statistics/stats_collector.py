"""
Statistics Collector
Gathers table, column, and index statistics from live PostgreSQL catalogs
or falls back smoothly to the high-fidelity mock catalog.
"""
import logging
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings
from app.statistics.mock_catalog import build_default_catalog
from app.statistics.stats_models import ColumnStatistics, DatabaseCatalog, TableStatistics

logger = logging.getLogger(__name__)

class StatisticsCollector:
    _instance_catalog: Optional[DatabaseCatalog] = None

    @classmethod
    def get_catalog(cls, scale: int = 10000, force_refresh: bool = False, db_id: Optional[str] = None) -> DatabaseCatalog:
        from app.statistics.database_manager import DatabaseManager
        db_mgr = DatabaseManager.get_instance()
        
        # If db_id specified or an active DB is set and not default postgres
        if db_id and db_id in db_mgr.databases:
            return db_mgr.databases[db_id].catalog
        
        active_db = db_mgr.get_active_db()
        if active_db and active_db.is_custom:
            return active_db.catalog

        if cls._instance_catalog is not None and not force_refresh:
            return cls._instance_catalog

        # Try to connect to live PostgreSQL
        try:
            conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                dbname=settings.POSTGRES_DB,
                connect_timeout=1
            )
            catalog = cls._load_from_postgres(conn)
            conn.close()
            if catalog and len(catalog.tables) > 0:
                cls._instance_catalog = catalog
                logger.info("Loaded live statistics from PostgreSQL catalog.")
                return catalog
        except Exception as e:
            logger.info(f"PostgreSQL connection not available or error ({e}). Using simulated catalog.")

        # Fallback to simulated catalog
        cls._instance_catalog = build_default_catalog(scale=scale)
        return cls._instance_catalog

    @classmethod
    def _load_from_postgres(cls, conn) -> DatabaseCatalog:
        catalog = DatabaseCatalog()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Query tables and page counts
            cur.execute("""
                SELECT 
                    c.relname AS table_name,
                    c.reltuples::bigint AS row_count,
                    c.relpages AS page_count
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relkind = 'r';
            """)
            tables = cur.fetchall()

            for t in tables:
                tname = t["table_name"].lower()
                row_cnt = max(1, t["row_count"])
                page_cnt = max(1, t["page_count"])
                tbl_stat = TableStatistics(
                    name=tname,
                    row_count=row_cnt,
                    page_count=page_cnt,
                    avg_row_width=100,
                    columns={},
                    indexes=[]
                )

                # Query column stats from pg_stats
                cur.execute("""
                    SELECT 
                        attname,
                        n_distinct,
                        null_frac,
                        avg_width
                    FROM pg_stats
                    WHERE tablename = %s;
                """, (tname,))
                cols = cur.fetchall()
                for c in cols:
                    cname = c["attname"].lower()
                    n_dist = c["n_distinct"]
                    if n_dist is None or n_dist == 0:
                        distinct_val = 1
                    elif n_dist < 0:
                        distinct_val = max(1, int(abs(n_dist) * row_cnt))
                    else:
                        distinct_val = max(1, int(n_dist))

                    tbl_stat.columns[cname] = ColumnStatistics(
                        name=cname,
                        data_type="varchar",
                        distinct_values=distinct_val,
                        null_fraction=float(c["null_frac"] or 0.0)
                    )

                # Query indexes
                cur.execute("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = %s;
                """, (tname,))
                indexes = cur.fetchall()
                for idx in indexes:
                    iname = idx["indexname"]
                    tbl_stat.indexes.append(iname)
                    # mark column as indexed if simple index
                    idef = idx["indexdef"].lower()
                    for cname in tbl_stat.columns:
                        if f"({cname})" in idef:
                            tbl_stat.columns[cname].has_index = True
                            tbl_stat.columns[cname].index_name = iname

                catalog.tables[tname] = tbl_stat

        return catalog
