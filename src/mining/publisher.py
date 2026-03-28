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

    def close(self) -> None:
        """Close the DB connection if open."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_tables(conn) -> None:
        """Verify factor_meta and factor_values tables exist. They should already
        exist from the DB restructure — this is a safety check only."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename FROM pg_tables
                WHERE tablename IN ('factor_meta', 'factor_values')
            """)
            existing = {r[0] for r in cur.fetchall()}
            if "factor_meta" not in existing or "factor_values" not in existing:
                raise RuntimeError(
                    f"Required tables missing: {{'factor_meta', 'factor_values'}} - {existing}. "
                    "Run scripts/restructure_db.py first."
                )

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
        """Upsert factor metadata and metrics into factor_meta."""
        s3 = factor_dict.get("stage3", {})
        rc = factor_dict.get("report_card", {})
        ic_is = s3.get("ic_mean_is")
        ic_oos = s3.get("ic_mean_oos")
        ic_mean = None
        if ic_is is not None and ic_oos is not None:
            ic_mean = (ic_is + ic_oos) / 2
        elif ic_is is not None:
            ic_mean = ic_is
        sql = """
            INSERT INTO factor_meta (
                factor_id, name, expression, category,
                ic_mean, ic_ir, ic_mean_is, ic_mean_oos, ic_win_rate,
                ls_return, monotonicity,
                max_corr, max_corr_with, batch_id, status,
                train_start, train_end, test_start, test_end,
                admitted_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
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
                max_corr     = EXCLUDED.max_corr,
                max_corr_with = EXCLUDED.max_corr_with,
                batch_id     = EXCLUDED.batch_id,
                status       = EXCLUDED.status,
                admitted_at  = EXCLUDED.admitted_at
        """
        params = (
            factor_id,
            factor_dict.get("name", f"factor_{factor_id}"),
            factor_dict.get("expression", ""),
            factor_dict.get("category", "other"),
            ic_mean,
            s3.get("ic_ir_is") or rc.get("ic_ir"),
            s3.get("ic_mean_is"),
            s3.get("ic_mean_oos"),
            s3.get("ic_win_rate"),
            s3.get("ls_return"),
            s3.get("monotonicity") or rc.get("monotonicity_is"),
            rc.get("max_corr"),
            rc.get("max_corr_factor"),
            factor_dict.get("batch"),
            "admitted",
            self.config.train_start,
            self.config.train_end,
            self.config.test_start,
            self.config.test_end,
            date.today(),
        )
        with conn.cursor() as cur:
            cur.execute(sql, params)

    def _save_values(self, conn, factor_id: str, factor_values: pd.DataFrame) -> None:
        """Delete existing values for factor, then bulk-insert into factor_values."""
        flat = self._to_flat_df(factor_values)
        factor_name = f"factor_{factor_id}"
        rows = [
            (t, sym, factor_name, v)
            for sym, t, v in zip(flat["symbol"], flat["time"], flat["value"])
            if pd.notna(v)
        ]
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM factor_values WHERE factor_name = %s",
                (factor_name,),
            )
            if rows:
                execute_values(
                    cur,
                    "INSERT INTO factor_values (time, symbol, factor_name, value) VALUES %s",
                    rows,
                    page_size=5000,
                )
        logger.info("Saved %d factor values for %s", len(rows), factor_name)

    def _generate_report(
        self,
        factor_id: str,
        factor_dict: dict,
        factor_values: pd.DataFrame,
    ) -> str:
        """Generate data-only HTML report using the report pipeline.

        Returns the path to the saved report, or empty string if generation fails.
        Failure is logged but not re-raised — report generation is non-transactional.
        """
        from report.builder import ReportDataBuilder
        from report.renderer import ReportRenderer

        report_dir = self.config.report_dir

        try:
            builder = ReportDataBuilder(factor_id, self.config)
            data = builder.build()

            empty_narrative = {
                "factor_metadata": {
                    "name_cn": "",
                    "expression_latex": factor_dict.get("expression", ""),
                },
            }

            renderer = ReportRenderer()
            path = renderer.render_to_file(data, empty_narrative, report_dir, factor_id)
            return path
        except Exception as e:
            logger.warning("Report generation failed for factor %s: %s", factor_id, e)
            return ""

    def _update_report_path(self, conn, factor_id: str, report_path: str) -> None:
        """Update factor_meta.report_path for the given factor_id."""
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE factor_meta SET report_path = %s WHERE factor_id = %s",
                (report_path, factor_id),
            )
