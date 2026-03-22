"""Factor publisher — DB persistence and HTML report generation for admitted factors."""

from __future__ import annotations

import logging
import os
from datetime import date

import pandas as pd
from psycopg2.extras import execute_values

from .config import MiningConfig

logger = logging.getLogger(__name__)


class FactorPublisher:
    """Persist an admitted factor to DB and generate an HTML report."""

    def __init__(self, config: MiningConfig):
        self.config = config
        self._conn = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_tables(conn) -> None:
        """Create tables if they do not exist. Idempotent — safe to call on every publish."""
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mining_factors (
                    factor_id    VARCHAR(10) PRIMARY KEY,
                    name         VARCHAR(200) NOT NULL,
                    expression   TEXT NOT NULL,
                    category     VARCHAR(50),
                    ic_mean      FLOAT,
                    ic_ir        FLOAT,
                    ic_mean_is   FLOAT,
                    ic_mean_oos  FLOAT,
                    ic_win_rate  FLOAT,
                    ls_return    FLOAT,
                    monotonicity FLOAT,
                    train_start  DATE,
                    train_end    DATE,
                    test_start   DATE,
                    test_end     DATE,
                    admitted_at  DATE NOT NULL,
                    report_path  VARCHAR(500)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mining_factor_values (
                    factor_id   VARCHAR(10) NOT NULL,
                    symbol      VARCHAR(20) NOT NULL,
                    trade_date  DATE NOT NULL,
                    value       DOUBLE PRECISION,
                    PRIMARY KEY (factor_id, symbol, trade_date)
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_mfv_factor_date
                    ON mining_factor_values (factor_id, trade_date)
            """)
        conn.commit()

    def publish(
        self,
        factor_id: str,
        factor_dict: dict,
        factor_values_is: pd.DataFrame,
        factor_values_oos: pd.DataFrame,
    ) -> str:
        """
        Publish an admitted factor.

        Steps 1–2 run in a single DB transaction.  Step 3 is non-transactional:
        report-generation failure is logged but does not roll back DB writes.

        Returns: path to the HTML report, or empty string if report generation failed.
        """
        conn = self._get_connection()
        self.ensure_tables(conn)

        try:
            combined = pd.concat([factor_values_is, factor_values_oos])
            combined = combined[~combined.index.duplicated(keep="last")]

            self._save_metrics(conn, factor_id, factor_dict)
            self._save_values(conn, factor_id, combined)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        # Non-transactional: generate HTML report
        report_path = self._generate_report(factor_id, factor_dict, combined)
        self._update_report_path(conn, factor_id, report_path)
        conn.commit()
        return report_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_connection(self):
        """Lazy psycopg2 connection using config.system.database.connection_string."""
        if self._conn is None:
            import psycopg2
            self._conn = psycopg2.connect(self.config.system.database.connection_string)
        return self._conn

    @staticmethod
    def _to_flat_df(qlib_df: pd.DataFrame) -> pd.DataFrame:
        """Convert Qlib MultiIndex (datetime, instrument) DataFrame to flat (time, symbol, value)."""
        df = qlib_df.iloc[:, [0]].reset_index()
        df.columns = ["time", "symbol", "value"]
        return df

    def _save_metrics(self, conn, factor_id: str, factor_dict: dict) -> None:
        """Upsert factor metadata and metrics into mining_factors."""
        metrics = factor_dict.get("metrics", {})
        sql = """
            INSERT INTO mining_factors (
                factor_id, name, expression, category,
                ic_mean, ic_ir, ic_mean_is, ic_mean_oos, ic_win_rate,
                ls_return, monotonicity,
                train_start, train_end, test_start, test_end,
                admitted_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s
            )
            ON CONFLICT (factor_id) DO UPDATE SET
                name         = EXCLUDED.name,
                expression   = EXCLUDED.expression,
                category     = EXCLUDED.category,
                ic_mean      = EXCLUDED.ic_mean,
                ic_ir        = EXCLUDED.ic_ir,
                ic_mean_is   = EXCLUDED.ic_mean_is,
                ic_mean_oos  = EXCLUDED.ic_mean_oos,
                ic_win_rate  = EXCLUDED.ic_win_rate,
                ls_return    = EXCLUDED.ls_return,
                monotonicity = EXCLUDED.monotonicity,
                train_start  = EXCLUDED.train_start,
                train_end    = EXCLUDED.train_end,
                test_start   = EXCLUDED.test_start,
                test_end     = EXCLUDED.test_end,
                admitted_at  = EXCLUDED.admitted_at
        """
        params = (
            factor_id,
            factor_dict.get("name", f"factor_{factor_id}"),
            factor_dict.get("expression", ""),
            factor_dict.get("category", "other"),
            metrics.get("ic_mean"),
            metrics.get("ic_ir"),
            metrics.get("ic_mean_is"),
            metrics.get("ic_mean_oos"),
            metrics.get("ic_win_rate"),
            metrics.get("ls_return"),
            metrics.get("monotonicity"),
            self.config.train_start,
            self.config.train_end,
            self.config.test_start,
            self.config.test_end,
            date.today(),
        )
        with conn.cursor() as cur:
            cur.execute(sql, params)

    def _save_values(self, conn, factor_id: str, factor_values: pd.DataFrame) -> None:
        """Delete existing values for factor_id, then bulk-insert new ones."""
        flat = self._to_flat_df(factor_values)
        rows = [
            (factor_id, sym, t, v)
            for sym, t, v in zip(flat["symbol"], flat["time"], flat["value"])
        ]
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mining_factor_values WHERE factor_id = %s",
                (factor_id,),
            )
            execute_values(
                cur,
                "INSERT INTO mining_factor_values (factor_id, symbol, trade_date, value) VALUES %s",
                rows,
                page_size=5000,
            )

    def _generate_report(
        self,
        factor_id: str,
        factor_dict: dict,
        factor_values: pd.DataFrame,
    ) -> str:
        """Convert factor values to flat format, load price data, and generate an HTML report.

        Returns the path to the saved report, or empty string if generation fails.
        Failure is logged but not re-raised — report generation is non-transactional.
        """
        from visualization.report import FactorReportGenerator

        flat_factor_df = self._to_flat_df(factor_values)

        report_dir = os.path.join(os.path.dirname(self.config.library_dir), "reports")
        os.makedirs(report_dir, exist_ok=True)

        factor_name = factor_dict.get("name", f"factor_{factor_id}")
        report_output_dir = os.path.join(report_dir, f"factor_{factor_id}")

        try:
            price_df = self._load_price_data(flat_factor_df)
            split_date = pd.Timestamp(self.config.test_start)

            gen = FactorReportGenerator(factor_name, report_output_dir)
            gen.analyze(flat_factor_df, price_df, split_date=split_date, n_groups=5)
            gen.generate_charts()
            saved = gen.save_charts(format="html")

            # Return the first saved path, or fallback if no charts were produced
            if saved:
                return next(iter(saved.values()))
            return os.path.join(report_output_dir, f"factor_{factor_id}.html")
        except Exception as e:
            logger.warning("Report generation failed for factor %s: %s", factor_id, e)
            return ""

    def _load_price_data(self, flat_factor_df: pd.DataFrame) -> pd.DataFrame:
        """Load close prices from price_daily for the symbols and date range in flat_factor_df."""
        symbols = flat_factor_df["symbol"].unique().tolist()
        start = flat_factor_df["time"].min()
        end = flat_factor_df["time"].max()
        sql = (
            "SELECT symbol, time, close FROM price_daily "
            "WHERE symbol = ANY(%s) AND time BETWEEN %s AND %s"
        )
        return pd.read_sql(sql, self._get_connection(), params=[symbols, start, end])

    def _update_report_path(self, conn, factor_id: str, report_path: str) -> None:
        """Update mining_factors.report_path for the given factor_id."""
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mining_factors SET report_path = %s WHERE factor_id = %s",
                (report_path, factor_id),
            )
