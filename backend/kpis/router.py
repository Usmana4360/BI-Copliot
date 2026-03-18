from fastapi import APIRouter, Depends
from backend.auth.router import get_current_user
from backend.utils.db import get_engine, run_sql

router = APIRouter(prefix="/kpis", tags=["kpis"])

def safe_query(sql):
    try:
        engine = get_engine()
        cols, rows = run_sql(engine, sql)
        return rows[0][0] if rows else None
    except Exception:
        return None

@router.get("/summary")
def kpi_summary(current_user: dict = Depends(get_current_user)):
    engine = get_engine()

    # Production rate — total units produced today
    production_rate = safe_query("""
        SELECT SUM(units_produced)
        FROM machine_production_daily
        WHERE production_date = CURRENT_DATE
    """)

    # Scrap rate — rejected / total * 100 (last 30 days)
    scrap_rate = safe_query("""
        SELECT ROUND(
            100.0 * SUM(rejected_units) / NULLIF(SUM(units_produced), 0), 1
        )
        FROM machine_production_daily
        WHERE production_date >= CURRENT_DATE - INTERVAL '30 days'
    """)

    # Downtime — total hours (last 7 days)
    downtime = safe_query("""
        SELECT ROUND(SUM(downtime_minutes) / 60.0, 1)
        FROM maintenance_logs
        WHERE log_date >= NOW() - INTERVAL '7 days'
    """)

    # MTTR — avg repair time per incident in hours
    mttr = safe_query("""
        SELECT ROUND(AVG(downtime_minutes) / 60.0, 1)
        FROM maintenance_logs
        WHERE log_date >= NOW() - INTERVAL '30 days'
    """)

    # MTBF — total uptime hours / number of failures (last 30 days)
    mtbf = safe_query("""
        SELECT ROUND(
            (30.0 * 24) / NULLIF(COUNT(*), 0), 1
        )
        FROM maintenance_logs
        WHERE log_date >= NOW() - INTERVAL '30 days'
    """)

    # OEE — quality ratio from production (last 7 days)
    oee = safe_query("""
        SELECT ROUND(
            100.0 * SUM(units_produced - rejected_units) / NULLIF(SUM(units_produced), 0), 1
        )
        FROM machine_production_daily
        WHERE production_date >= CURRENT_DATE - INTERVAL '7 days'
    """)

    return {
        "oee":             oee,
        "mtbf":            mtbf,
        "mttr":            mttr,
        "downtime":        downtime,
        "scrap_rate":      scrap_rate,
        "production_rate": production_rate,
    }


@router.get("/oee-trend")
def oee_trend(current_user: dict = Depends(get_current_user)):
    try:
        engine = get_engine()
        cols, rows = run_sql(engine, """
            SELECT
                TO_CHAR(production_date, 'Dy') AS day,
                ROUND(
                    100.0 * SUM(units_produced - rejected_units)
                    / NULLIF(SUM(units_produced), 0), 1
                ) AS oee
            FROM machine_production_daily
            WHERE production_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY production_date
            ORDER BY production_date
        """)
        return [{"day": r[0], "oee": float(r[1])} for r in rows]
    except Exception:
        return []


@router.get("/downtime-breakdown")
def downtime_breakdown(current_user: dict = Depends(get_current_user)):
    try:
        engine = get_engine()
        cols, rows = run_sql(engine, """
            SELECT
                issue_type,
                SUM(downtime_minutes) AS total_minutes
            FROM maintenance_logs
            WHERE log_date >= NOW() - INTERVAL '30 days'
            GROUP BY issue_type
            ORDER BY total_minutes DESC
            LIMIT 5
        """)
        return [{"name": r[0], "value": int(r[1])} for r in rows]
    except Exception:
        return []

