"""Factor DB persistence: write admitted factors to TimescaleDB.

Handles two tables:
  - factor_meta: factor metadata (expression, metrics, status)
  - factor_values: time-series factor values (time, symbol, factor_name, value)

Also provides a read path for the DataProvider cache hierarchy:
  parquet cache → DB factor_values → Qlib compute
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default DB connection params (same as the rest of the system)
_DEFAULT_DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "dbname": "quant_data",
    "user": "postgres",
    "password": "postgres",
}


def _get_conn(db_params: Optional[Dict] = None):
    """Get a psycopg2 connection."""
    import psycopg2
    params = db_params or _DEFAULT_DB_PARAMS
    return psycopg2.connect(**params)


# ---------------------------------------------------------------------------
# Write: factor_meta
# ---------------------------------------------------------------------------

def write_factor_meta(
    factor_id: str,
    name: str,
    expression: str,
    metrics: Dict[str, Any],
    batch_id: str = "",
    status: str = "admitted",
    db_params: Optional[Dict] = None,
) -> None:
    """Upsert a row into factor_meta."""
    conn = _get_conn(db_params)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO factor_meta (
                    factor_id, name, expression, category,
                    ic_mean, ic_ir, ic_mean_is, ic_mean_oos,
                    ic_win_rate, ls_return, monotonicity,
                    train_start, train_end, test_start, test_end,
                    admitted_at, max_corr, max_corr_with, batch_id, status
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    CURRENT_DATE, %s, %s, %s, %s
                )
                ON CONFLICT (factor_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    expression = EXCLUDED.expression,
                    ic_mean = EXCLUDED.ic_mean,
                    ic_ir = EXCLUDED.ic_ir,
                    ic_mean_is = EXCLUDED.ic_mean_is,
                    ic_mean_oos = EXCLUDED.ic_mean_oos,
                    ic_win_rate = EXCLUDED.ic_win_rate,
                    ls_return = EXCLUDED.ls_return,
                    monotonicity = EXCLUDED.monotonicity,
                    max_corr = EXCLUDED.max_corr,
                    max_corr_with = EXCLUDED.max_corr_with,
                    batch_id = EXCLUDED.batch_id,
                    status = EXCLUDED.status,
                    admitted_at = CURRENT_DATE
            """, (
                factor_id, name, expression, metrics.get("category", ""),
                metrics.get("ic_mean"), metrics.get("ic_ir"),
                metrics.get("ic_mean_train"), metrics.get("ic_mean_validation"),
                metrics.get("ic_win_rate_validation"), metrics.get("ls_mean"),
                metrics.get("monotonicity_validation"),
                metrics.get("train_start", "2015-01-01"),
                metrics.get("train_end", "2021-12-31"),
                metrics.get("test_start", "2022-01-01"),
                metrics.get("test_end", "2023-12-31"),
                metrics.get("max_lib_corr"), metrics.get("nearest_factor_id"),
                batch_id, status,
            ))
        conn.commit()
        logger.info("Wrote factor_meta for %s", factor_id)
    except Exception as exc:
        conn.rollback()
        logger.error("Failed to write factor_meta for %s: %s", factor_id, exc)
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Write: factor_values (bulk COPY for speed)
# ---------------------------------------------------------------------------

def write_factor_values(
    factor_id: str,
    factor_df: pd.DataFrame,
    db_params: Optional[Dict] = None,
) -> int:
    """Bulk-write factor values to the factor_values table using COPY.

    Parameters
    ----------
    factor_id : str
        Factor ID (e.g. "F001"). Stored as "factor_001" in the table.
    factor_df : pd.DataFrame
        MultiIndex (instrument/datetime or datetime/instrument) with a single
        value column. Or flat DataFrame with [time, symbol, value].

    Returns
    -------
    int : number of rows written
    """
    from core.factor_stats import multiindex_to_flat

    # Normalize to flat format
    if isinstance(factor_df.index, pd.MultiIndex):
        flat = multiindex_to_flat(factor_df)
    elif "time" in factor_df.columns and "symbol" in factor_df.columns:
        flat = factor_df[["time", "symbol", "value"]].copy()
    else:
        raise ValueError("factor_df must have MultiIndex or [time, symbol, value] columns")

    flat = flat.dropna(subset=["value"])
    if flat.empty:
        return 0

    # Factor name in DB convention: "factor_001"
    numeric_part = factor_id.lstrip("F").lstrip("0") or "0"
    factor_name = f"factor_{numeric_part.zfill(3)}"

    flat["factor_name"] = factor_name

    conn = _get_conn(db_params)
    try:
        with conn.cursor() as cur:
            # Delete existing values for this factor
            cur.execute(
                "DELETE FROM factor_values WHERE factor_name = %s",
                (factor_name,),
            )

            # Bulk COPY via StringIO
            buf = io.StringIO()
            for _, row in flat.iterrows():
                t = pd.Timestamp(row["time"]).strftime("%Y-%m-%d %H:%M:%S")
                buf.write(f"{t}\t{row['symbol']}\t{factor_name}\t{row['value']}\n")
            buf.seek(0)

            cur.copy_from(
                buf,
                "factor_values",
                columns=("time", "symbol", "factor_name", "value"),
                sep="\t",
            )

        conn.commit()
        n = len(flat)
        logger.info("Wrote %d rows to factor_values for %s (%s)", n, factor_id, factor_name)
        return n
    except Exception as exc:
        conn.rollback()
        logger.error("Failed to write factor_values for %s: %s", factor_id, exc)
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read: factor_values (for DataProvider cache hierarchy)
# ---------------------------------------------------------------------------

def read_factor_values(
    expression: str,
    start: str,
    end: str,
    factor_id: Optional[str] = None,
    db_params: Optional[Dict] = None,
) -> Optional[pd.DataFrame]:
    """Try to read pre-computed factor values from DB.

    Looks up the expression in factor_meta to find the factor_name,
    then reads from factor_values.

    Returns None if the factor is not in DB.
    Returns a MultiIndex DataFrame (datetime, instrument) if found.
    """
    conn = _get_conn(db_params)
    try:
        with conn.cursor() as cur:
            if factor_id:
                numeric_part = factor_id.lstrip("F").lstrip("0") or "0"
                factor_name = f"factor_{numeric_part.zfill(3)}"
            else:
                # Look up by expression
                cur.execute(
                    "SELECT factor_id FROM factor_meta WHERE expression = %s AND status = 'admitted' LIMIT 1",
                    (expression,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                fid = row[0]
                numeric_part = fid.lstrip("F").lstrip("0") or "0"
                factor_name = f"factor_{numeric_part.zfill(3)}"

            # Read values
            df = pd.read_sql(
                "SELECT time, symbol, value FROM factor_values "
                "WHERE factor_name = %s AND time BETWEEN %s AND %s",
                conn,
                params=(factor_name, f"{start} 00:00:00", f"{end} 23:59:59"),
            )

        if df.empty:
            return None

        # Convert to MultiIndex format matching Qlib output
        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index(["time", "symbol"])
        df.index.names = ["datetime", "instrument"]
        df.columns = [expression]
        return df

    except Exception as exc:
        logger.debug("DB read failed for expression '%s': %s", expression, exc)
        return None
    finally:
        conn.close()
