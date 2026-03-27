"""Batch-publish all library factors to DB so the report builder can use them."""
from __future__ import annotations

import logging
import sys
import yaml

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    from mining.config import MiningConfig
    from mining.operators import register_custom_operators
    from mining.publisher import FactorPublisher

    import qlib
    from qlib.config import C
    from qlib.data import D

    config = MiningConfig()

    # Init Qlib
    if not getattr(qlib, "_is_initialized", False):
        qlib.init(provider_uri=config.qlib_data_dir)
    register_custom_operators()
    C.kernels = 1

    # Load library
    import os
    lib_yaml = os.path.join(config.library_dir, "library.yaml")
    with open(lib_yaml) as f:
        lib = yaml.safe_load(f)
    factors = lib.get("factors", [])
    logger.info("Library has %d factors", len(factors))

    # Resolve universe
    instruments = D.instruments(config.universe)

    publisher = FactorPublisher(config)

    for fac in factors:
        fid = fac["id"]
        expr = fac["expression"]
        name = fac["name"]

        # Check if already published
        conn = publisher._get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM mining_factor_values WHERE factor_id = %s", (fid,))
            count = cur.fetchone()[0]
        if count > 0:
            logger.info("Factor %s (%s) already has %d rows, skipping", fid, name, count)
            continue

        logger.info("Computing factor %s (%s): %s", fid, name, expr)
        try:
            # Compute IS values
            vals_is = D.features(
                instruments=instruments,
                fields=[expr],
                start_time=config.train_start,
                end_time=config.train_end,
            )
            # Compute OOS values
            vals_oos = D.features(
                instruments=instruments,
                fields=[expr],
                start_time=config.test_start,
                end_time=config.test_end,
            )
            # Qlib returns MultiIndex (instrument, datetime) — swap to (datetime, instrument)
            # so publisher._to_flat_df produces correct column order
            vals_is = vals_is.swaplevel().sort_index()
            vals_oos = vals_oos.swaplevel().sort_index()
            vals_is.index.names = ["datetime", "instrument"]
            vals_oos.index.names = ["datetime", "instrument"]
            logger.info("  IS: %d rows, OOS: %d rows", len(vals_is), len(vals_oos))

            # Load factor YAML for full metadata
            factor_yaml_path = f"mining/library/factors/factor_{fid}.yaml"
            with open(factor_yaml_path) as f:
                factor_meta = yaml.safe_load(f)

            # Build factor_dict compatible with publisher
            metrics = factor_meta.get("metrics", {})
            factor_dict = {
                "name": name,
                "expression": expr,
                "category": fac.get("category", "other"),
                "stage3": {
                    "ic_mean_is": metrics.get("ic_mean_is"),
                    "ic_mean_oos": metrics.get("ic_mean_oos"),
                    "ic_ir_is": metrics.get("ic_ir_is"),
                    "ic_win_rate": metrics.get("ic_win_rate"),
                    "ls_return": metrics.get("ls_return"),
                    "monotonicity": metrics.get("monotonicity"),
                },
            }

            publisher.publish(fid, factor_dict, vals_is, vals_oos)
            logger.info("  Published factor %s (%s)", fid, name)

        except Exception as e:
            logger.error("  FAILED factor %s: %s", fid, e)
            continue

    publisher.close()
    logger.info("Done")


if __name__ == "__main__":
    main()
