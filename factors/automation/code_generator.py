"""Generate factor Python code from `FactorInfo`."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .factor_extractor import FactorInfo

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Generate code skeletons for extracted factors."""

    def __init__(self) -> None:
        self._logger = logger

    def generate(self, factor_info: FactorInfo, output_path: Optional[str] = None) -> str:
        """
        Generate factor code from `FactorInfo`.

        Args:
            factor_info: structured factor config
            output_path: optional destination file path

        Returns:
            generated python source code
        """
        class_name = "".join(part.capitalize() for part in factor_info.name.split("_")) + "Factor"
        params_signature = ", ".join(f"{k}={repr(v)}" for k, v in factor_info.parameters.items())
        if params_signature:
            params_signature = ", " + params_signature

        code = f'''"""Auto-generated factor: {factor_info.display_name}."""\n\nimport pandas as pd\nfrom quant_factor_system.core.base import Factor\n\n\nclass {class_name}(Factor):\n    """{factor_info.description}"""\n\n    def __init__(self{params_signature}, description: str = {factor_info.description!r}):\n        super().__init__({factor_info.name!r}, description)\n'''

        for key, value in factor_info.parameters.items():
            code += f"        self.{key} = {repr(value)}\n"

        code += f"""\n    def calculate(self, data: pd.DataFrame) -> pd.Series:\n        # Formula: {factor_info.formula}\n        # Logic: {factor_info.logic[:200]}\n"""

        if factor_info.formula:
            code += (
                "        factor = data.eval("
                f"{factor_info.formula!r}, engine='python') if not data.empty else pd.Series(dtype=float)\n"
                "        self.values = factor\n"
                "        return factor\n"
            )
        else:
            code += (
                "        raise NotImplementedError('Please implement factor calculation logic manually')\n"
            )

        if output_path:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(code, encoding="utf-8")
            self._logger.info("Generated factor code file: %s", output)
        else:
            self._logger.info("Generated factor code for: %s", factor_info.name)

        return code

