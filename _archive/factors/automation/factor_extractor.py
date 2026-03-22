"""Extract factor definitions from parsed PDF text."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


@dataclass
class FactorInfo:
    """Structured factor definition extracted from PDF."""

    name: str
    display_name: str
    formula: str
    description: str
    category: str
    frequency: str
    data_requirements: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    logic: str = ""


class FactorExtractor:
    """Extract `FactorInfo` entries from PDF parser output."""

    _FIELD_PATTERNS = {
        "name": [r"(?:factor\s*name|name|因子名称)\s*[:：]\s*(.+)"],
        "display_name": [r"(?:display\s*name|显示名称|中文名)\s*[:：]\s*(.+)"],
        "formula": [r"(?:formula|公式)\s*[:：]\s*(.+)"],
        "description": [r"(?:description|描述|说明)\s*[:：]\s*(.+)"],
        "category": [r"(?:category|类别|分类)\s*[:：]\s*(.+)"],
        "frequency": [r"(?:frequency|频率|调仓频率)\s*[:：]\s*(.+)"],
        "logic": [r"(?:logic|method|计算逻辑|逻辑)\s*[:：]\s*([\s\S]+)"],
    }

    def __init__(self) -> None:
        self._logger = logger

    def extract(self, parsed_content: Union[str, Dict[str, Any]]) -> List[FactorInfo]:
        """Extract one or multiple factors from parsed PDF text."""
        text = parsed_content if isinstance(parsed_content, str) else parsed_content.get("text", "")
        if not text.strip():
            self._logger.warning("Empty content received by FactorExtractor")
            return []

        chunks = self._split_factor_chunks(text)
        factors: List[FactorInfo] = []
        for idx, chunk in enumerate(chunks, start=1):
            info = self._extract_single(chunk, default_index=idx)
            factors.append(info)

        self._logger.info("Extracted %d factor(s) from document", len(factors))
        return factors

    def _split_factor_chunks(self, text: str) -> List[str]:
        markers = list(
            re.finditer(
                r"(?:^|\n)\s*(?:factor\s*name|name|因子名称)\s*[:：]",
                text,
                flags=re.IGNORECASE,
            )
        )
        if len(markers) <= 1:
            return [text]

        chunks: List[str] = []
        for i, marker in enumerate(markers):
            start = marker.start()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            chunks.append(text[start:end])
        return chunks

    def _extract_single(self, text: str, default_index: int) -> FactorInfo:
        parsed: Dict[str, str] = {}
        for field_name, patterns in self._FIELD_PATTERNS.items():
            value = ""
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    value = match.group(1).strip().splitlines()[0].strip()
                    break
            parsed[field_name] = value

        display_name = parsed["display_name"] or parsed["name"] or f"factor_{default_index}"
        name = self._normalize_name(parsed["name"] or display_name, default_index=default_index)
        formula = parsed["formula"] or self._guess_formula(text)
        description = parsed["description"] or self._guess_description(text)
        category = parsed["category"] or self._infer_category(text)
        frequency = parsed["frequency"] or self._infer_frequency(text)
        data_requirements = self._infer_data_requirements(text)
        parameters = self._infer_parameters(text)
        logic = parsed["logic"] or self._extract_logic(text)

        return FactorInfo(
            name=name,
            display_name=display_name,
            formula=formula,
            description=description,
            category=category,
            frequency=frequency,
            data_requirements=data_requirements,
            parameters=parameters,
            logic=logic,
        )

    def _normalize_name(self, value: str, default_index: int) -> str:
        candidate = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
        if not candidate:
            candidate = f"factor_{default_index}"
        if candidate[0].isdigit():
            candidate = f"factor_{candidate}"
        return candidate

    def _guess_formula(self, text: str) -> str:
        match = re.search(r"(?:公式|formula)\s*[:：]?\s*([^\n]+)", text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else "close.pct_change(1)"

    def _guess_description(self, text: str) -> str:
        first_non_empty = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first_non_empty[:300] if first_non_empty else "Auto extracted factor."

    def _infer_category(self, text: str) -> str:
        lower = text.lower()
        if "volatility" in lower or "波动" in text:
            return "volatility"
        if "return" in lower or "收益" in text or "momentum" in lower:
            return "return"
        if "volume" in lower or "成交量" in text:
            return "volume"
        return "custom"

    def _infer_frequency(self, text: str) -> str:
        lower = text.lower()
        if "minute" in lower or "分钟" in text or "1min" in lower:
            return "minute"
        if "week" in lower or "周" in text:
            return "weekly"
        if "month" in lower or "月" in text:
            return "monthly"
        return "daily"

    def _infer_data_requirements(self, text: str) -> List[str]:
        fields = ["open", "high", "low", "close", "volume", "amount", "vwap"]
        found = [field for field in fields if re.search(rf"\b{field}\b", text, flags=re.IGNORECASE)]
        return found or ["close"]

    def _infer_parameters(self, text: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for key, value in re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+(?:\.[0-9]+)?)", text):
            params[key] = int(value) if value.isdigit() else float(value)
        return params

    def _extract_logic(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines[:8])

