---
name: plan-precision-requirements
description: Plans must verify exact API signatures, data availability, unit compatibility, and not assume fields/params exist without checking actual code
type: feedback
---

Plans must be precise against actual codebase state, not assumed interfaces.

**Why:** User rejected a Barra model plan twice because it assumed DataProvider had a `universe` param it doesn't have, used wrong units (calendar vs trading days), proposed changing existing pure function return keys (breaking tests), assumed industry data exists without verifying, and used inconsistent terminology (MAD vs std).

**How to apply:**
- Before writing any plan that calls existing functions, READ the actual function signature and verify params exist
- When specifying time durations, be explicit about trading days vs calendar days and verify against data provider behavior
- Never propose changing pure function return schemas — do schema mapping in the orchestrator layer
- If data availability is uncertain (e.g. industry codes), explicitly check and state "not available, degrade gracefully"
- Use the same terminology as existing code (e.g. preprocess.py uses std not MAD)
