#!/usr/bin/env python3
"""Reflect script for batch_042."""

from research.logic.reflect import (
    apply_belief_delta, write_reflection_md, save_global_escalation,
    recompute_research_state, LogicBeliefDelta, GlobalEscalationDelta
)
from pathlib import Path

# L004 Delta
delta_l004 = LogicBeliefDelta(
    logic_id='L004',
    batch_id='batch_042',
    status_change=None,
    families_to_add=[],
    families_to_remove=[],
    ops_to_add=[],
    avoid_patterns_to_add=[
        'Triple encoding with Mul(amtra_rank, tur_rank) — max_lib_corr=0.591 with F004, elevated redundancy'
    ],
    focus_question_update='Triple encoding (C001 reserve) shows strong ICIR but elevated redundancy with existing subspace. Need to determine if the third rank dimension adds genuine orthogonal signal. Next: try simpler dual-encoding amount x rel-tur at different scales.',
    generated_this_batch=1,
    admits_this_batch=0,
    bottleneck_update='C001 (triple encoding) reserved: ICIR_val=-0.588, ICIR_ho=-0.369, Mono=-0.9, but max_lib_corr=0.591 with F004 (elevated redundancy). Barra_res=-0.299 borderline. Need holdout to confirm orthogonality.',
    threads_to_add=[],
    threads_to_update=[
        {
            'id': 'T003',
            'question': 'Can amount x vol-competition conditioning be combined with tur rank for dual-encoding?',
            'why_matters': 'C001 (triple encoding) shows strong stats but elevated redundancy (max_lib_corr=0.591). Need to isolate if third rank adds orthogonal value.',
            'status': 'active',
            'priority': 'high',
            'next_probes': [
                'Mul(Corr($close,$amount,10),Div(CsRank($turnover_rate),CsRank($volume)))',
                'Mul(Corr($close,$amount,20),Div(CsRank($amount),CsRank($volume))) — dual encoding baseline'
            ],
            'stop_condition': 'If triple encoding is redundant, try dual encoding at different scales'
        }
    ],
    threads_to_park=[],
    next_actions=[
        'Probe 10d amount x rel-tur: Mul(Corr($close,$amount,10),Div(CsRank($turnover_rate),CsRank($volume)))',
        'Probe dual encoding baseline: Mul(Corr($close,$amount,20),Div(CsRank($amount),CsRank($volume)))'
    ]
)

# L001 Delta
delta_l001 = LogicBeliefDelta(
    logic_id='L001',
    batch_id='batch_042',
    status_change=None,
    families_to_add=[],
    families_to_remove=[],
    ops_to_add=[],
    avoid_patterns_to_add=[
        'Shadow x pv_corr — alpha_surv=0.138, turnover_20d exposure=0.271, style absorbed',
        'Shadow x vol-competition — mono sign flip, dominant_style=log_circ_cap (size proxy)'
    ],
    focus_question_update='Shadow x Amihud (F002) is the ONLY confirmed mechanism. pv_corr and vol-competition both fail. Need to explore shadow AS FILTER or alternative shadow definitions (upper/lower shadow only).',
    generated_this_batch=2,
    admits_this_batch=0,
    bottleneck_update='C002 (shadow x pv_corr): alpha_surv=0.138, turnover_20d exposure=0.271. C003 (shadow x vol-competition): mono sign flip, size proxy. Both failures confirm shadow ONLY works with Amihud cost-of-trading.',
    threads_to_add=[
        {
            'id': 'T004',
            'question': 'Can upper/lower shadow components be used separately as Amihud conditioning?',
            'why_matters': 'F002 uses full shadow. Separating upper (informed buying) vs lower (selling pressure) shadow could reveal direction-specific microstructure signals.',
            'status': 'active',
            'priority': 'medium',
            'next_probes': [
                'Mul(UpperShadowRatio,Div($amount,Mean($volume,20)))',
                'Mul(LowerShadowRatio,Div($amount,Mean($volume,20)))'
            ],
            'stop_condition': 'If upper/lower shadow x Amihud produces alpha_surv > 0.35 and directional signal, confirm component-level microstructure'
        }
    ],
    threads_to_update=[
        {
            'id': 'T002',
            'question': 'Can shadow be combined with pv_corr or vol-competition instead of Amihud?',
            'why_matters': 'Both shadow x pv_corr (alpha_surv=0.138) and shadow x vol-competition (size proxy) failed. Confirmed: only Amihud provides orthogonal conditioning.',
            'status': 'parked',
            'priority': 'high',
            'next_probes': [],
            'stop_condition': 'stop_condition met — pv_corr and vol-competition both confirmed non-viable'
        }
    ],
    threads_to_park=['T002'],
    next_actions=[
        'Probe upper shadow x Amihud: Mul(UpperShadowRatio,Div($amount,Mean($volume,20)))',
        'Probe lower shadow x Amihud: Mul(LowerShadowRatio,Div($amount,Mean($volume,20)))'
    ]
)

apply_belief_delta(Path('storage/logic/cards/L004.yaml'), delta_l004)
print('L004 card updated')

apply_belief_delta(Path('storage/logic/cards/L001.yaml'), delta_l001)
print('L001 card updated')

narrative_l004 = """## Batch batch_042 — 2026-04-07

**Logic**: L004
**Generated**: 1  |  **Admitted**: 0 | **Reserve**: 1 (C001)
**Bottleneck**: Triple encoding (C001) shows excellent ICIR (-0.588 val, -0.369 ho) but elevated redundancy (max_lib_corr=0.591). Need to determine if triple encoding adds genuine orthogonal signal or just complicates existing subspace.
**Next actions**:
- Probe 10d amount x rel-tur
- Probe dual encoding baseline

### Thesis Update
Triple encoding (pv_corr x amount_rank/vol_rank x tur_rank) produces strong validation metrics but with elevated redundancy. The question is whether the third rank dimension adds genuine orthogonal signal. Holdout shows excellent stability (decay=0.912).

### Evidence
- **支持**: C001 ICIR_val=-0.588, ICIR_ho=-0.369 (strong)
- **支持**: C001 Mono_val=-0.9, Mono_ho=-0.9 (excellent stability)
- **支持**: C001 holdout_decay=0.912 (very stable)
- **反对**: C001 max_lib_corr=0.591 — elevated redundancy with F004
- **反对**: C001 Barra_res=-0.299 (borderline)

### Failure Boundary
None new for L004. Triple encoding is a valid probe.

### Open Questions
1. Is triple encoding genuinely orthogonal, or additive variant in existing subspace?
2. Does adding amount_rank actually change the information captured?

### Next Probes
- `Mul(Corr($close,$amount,10),Div(CsRank($turnover_rate),CsRank($volume)))` — 10d scale
- `Mul(Corr($close,$amount,20),Div(CsRank($amount),CsRank($volume)))` — dual encoding baseline
"""

narrative_l001 = """## Batch batch_042 — 2026-04-07

**Logic**: L001
**Generated**: 2  |  **Admitted**: 0 | **Reject**: 2 (C002, C003)
**Bottleneck**: Both new routes failed. Shadow ONLY works with Amihud. Need to explore shadow AS FILTER or component-level shadow definitions.
**Next actions**:
- Probe upper shadow x Amihud
- Probe lower shadow x Amihud

### Thesis Update
Both new shadow routes confirmed dead:
1. Shadow x pv_corr: alpha_surv=0.138 — shadow absorbed by turnover_20d style
2. Shadow x vol-competition: mono sign flip — size proxy, not microstructure
Both failures confirm: shadow MUST be conditioned on Amihud (cost-of-trading). Only confirmed mechanism is F002 (shadow x Amihud).

### Evidence
- **支持**: F002 (shadow x Amihud): alpha_surv=0.377, Barra_res=-0.176 — confirmed
- **反对**: C002 alpha_surv=0.138 — pv_corr does NOT provide orthogonal conditioning
- **反对**: C003 mono flips: vol-competition is size proxy, not microstructure

### Failure Boundary
Shadow x pv_corr: does not work (turnover_20d absorption).
Shadow x vol-competition: does not work (size proxy).
Do not retry shadow x pv_corr or shadow x vol-competition.

### Open Questions
1. Can upper/lower shadow components work as directional Amihud conditioning?
2. Can shadow be used AS FILTER rather than primary signal?

### Next Probes
- `Mul(UpperShadowRatio,Div($amount,Mean($volume,20)))` — upper shadow x Amihud
- `Mul(LowerShadowRatio,Div($amount,Mean($volume,20)))` — lower shadow x Amihud
"""

write_reflection_md(Path('storage/logic/reflections/L004.md'), delta_l004, narrative_l004)
write_reflection_md(Path('storage/logic/reflections/L001.md'), delta_l001, narrative_l001)
print('Reflections written')

esc = GlobalEscalationDelta(
    batch_id='batch_042',
    status='applied',
    proposed_lessons=[
        {
            'id': 'FP-L001-shadow-x-pv-corr',
            'category': 'false_positive',
            'lesson': 'Shadow x pv_corr: alpha_surv=0.138, turnover_20d exposure=0.271. pv_corr does not provide orthogonal conditioning for shadow.'
        },
        {
            'id': 'FP-L001-shadow-x-vol-competition',
            'category': 'false_positive',
            'lesson': 'Shadow x vol-competition: mono sign flip, dominant_style=log_circ_cap (size). Not a shadow mechanism.'
        }
    ],
    proposed_forbidden=[],
    logic_proposals=[],
    saturation_signal=False
)
save_global_escalation(Path('storage/state/global_escalation.yaml'), esc)
print('Global escalation saved')

recompute_research_state(Path('storage/logic/cards'), Path('storage/state/research_state.yaml'))
print('State recomputed')
print('Reflect complete')
