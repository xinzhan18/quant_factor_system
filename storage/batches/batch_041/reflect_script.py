#!/usr/bin/env python3
"""Reflect script for batch_041."""

from research.logic.reflect import apply_belief_delta, write_reflection_md, save_global_escalation, LogicBeliefDelta, GlobalEscalationDelta
from pathlib import Path

# L004 Delta
delta_l004 = LogicBeliefDelta(
    logic_id='L004',
    batch_id='batch_041',
    status_change=None,
    families_to_add=[],
    families_to_remove=[],
    ops_to_add=[],
    avoid_patterns_to_add=[
        'Div(CsRank($amount),CsRank($volume)) without pv_corr — pure vol-competition fails holdout (sign flip)'
    ],
    focus_question_update='Amount x vol-competition conditioning (amount_rank/vol_rank) confirmed. Pure vol-competition without pv_corr fails. Next: explore combined tur+amount vol-competition conditioning and amount-tur divergence.',
    generated_this_batch=3,
    admits_this_batch=1,
    bottleneck_update='amount x vol-competition (C002) admits: Barra_res=-0.270, Mono=-0.9. Pure vol-competition (C003) fails holdout (sign flip, decay=0.445). pv_corr is essential component. C001 duplicate of F010 rejected.',
    threads_to_add=[
        {
            'id': 'T003',
            'question': 'Can amount x vol-competition conditioning be combined with tur rank for dual-encoding?',
            'why_matters': 'F010 uses tur_rank/vol_rank, C002 uses amount_rank/vol_rank. Both work. Can combining both rank dimensions produce orthogonal signal?',
            'status': 'active',
            'priority': 'high',
            'next_probes': [
                'Mul(Corr($close,$amount,20),Mul(Div(CsRank($amount),CsRank($volume)),CsRank($turnover_rate)))',
                'Mul(Corr($close,$amount,20),Sub(CsRank($amount),CsRank($turnover_rate)))'
            ],
            'stop_condition': 'If combined encoding produces Barra_res < -0.3 and alpha_surv > 0.4'
        }
    ],
    threads_to_update=[],
    threads_to_park=[],
    next_actions=[
        'Probe combined amount x vol-competition x tur rank triple encoding',
        'Probe amount minus tur rank divergence'
    ]
)

# L001 Delta
delta_l001 = LogicBeliefDelta(
    logic_id='L001',
    batch_id='batch_041',
    status_change=None,
    families_to_add=[],
    families_to_remove=[],
    ops_to_add=[],
    avoid_patterns_to_add=[
        'Shadow x Amihud with same expression as F002 — duplicate',
        'Any shadow variant using Div($amount,Mean($volume,20)) as conditioning — same as F002'
    ],
    focus_question_update='shadow x Amihud (F002) fully explored. C004 is duplicate. Need new shadow mechanism NOT using Amihud as partner.',
    generated_this_batch=1,
    admits_this_batch=0,
    bottleneck_update='C004 is expression duplicate of F002. shadow x Amihud already admitted. L001 needs new shadow mechanism ideas.',
    threads_to_add=[],
    threads_to_update=[
        {
            'id': 'T002',
            'question': 'Can shadow be combined with pv_corr or vol-competition instead of Amihud?',
            'why_matters': 'F002 (shadow x Amihud) is only confirmed shadow mechanism. All other shadow pairings fail. Need fundamentally new shadow interaction.',
            'status': 'active',
            'priority': 'high',
            'next_probes': [
                'Mul(ShadowRatio,Corr($close,$amount,20))',
                'Mul(ShadowRatio,Div(CsRank($turnover_rate),CsRank($volume)))'
            ],
            'stop_condition': 'If shadow x vol-competition or shadow x pv_corr produces alpha_surv > 0.35'
        }
    ],
    threads_to_park=[],
    next_actions=[
        'Probe shadow x pv_corr interaction (not Amihud)',
        'Probe shadow x volume competition conditioning'
    ]
)

apply_belief_delta(Path('storage/logic/cards/L004.yaml'), delta_l004)
print('L004 card updated')

apply_belief_delta(Path('storage/logic/cards/L001.yaml'), delta_l001)
print('L001 card updated')

narrative_l004 = """## Batch batch_041 — 2026-04-07

**Logic**: L004
**Generated**: 3  |  **Admitted**: 1 (C002=amount x vol-competition)
**Bottleneck**: Amount x vol-competition conditioning confirmed (C002 admit: Barra_res=-0.270, Mono=-0.9). Pure vol-competition without pv_corr (C003) fails holdout with sign flip. C001 duplicate of F010 rejected.
**Next actions**:
- Probe combined tur+amount vol-competition conditioning
- Probe amount minus tur rank divergence

### Thesis Update
Amount x vol-competition conditioning (amount_rank / volume_rank) is a confirmed new mechanism distinct from F010's tur_rank / volume_rank. The monetary volume competition encoding captures "smart money per unit volume activity" differently from pure turnover competition. C002 admits with Barra_res=-0.270 and Mono=-0.9 on both val and holdout.

### Evidence
- **支持**: C002 admit: ICIR_val=-0.558, Barra_res=-0.270, Mono_val=-0.9, Mono_ho=-0.9
- **支持**: C002 amount x vol-competition conditioning confirmed as distinct from F010's tur x vol-competition
- **反对**: C001 rejected as duplicate of F010 (identical expression)
- **反对**: C003 rejected: pure vol-competition without pv_corr fails holdout (sign flip, decay=0.445)

### Failure Boundary
Pure vol-competition signal (Div(CsRank(amount),CsRank(volume)) without pv_corr) is insufficient. C003 failed holdout with sign flip. The pv_corr component is essential for signal survival — it provides the price discovery dimension that pure volume competition lacks.

### Open Questions
1. Is amount x vol-competition a distinct mechanism from tur x vol-competition, or just a correlated variant?
2. Can we combine both tur_rank and amount_rank in conditioning for orthogonal signal?

### Next Probes
- `Mul(Corr($close,$amount,20),Mul(Div(CsRank($amount),CsRank($volume)),CsRank($turnover_rate)))` — combined encoding
- `Mul(Corr($close,$amount,20),Sub(CsRank($amount),CsRank($turnover_rate)))` — rank divergence
"""

narrative_l001 = """## Batch batch_041 — 2026-04-07

**Logic**: L001
**Generated**: 1  |  **Admitted**: 0
**Bottleneck**: C004 is duplicate of F002 (identical expression). shadow x Amihud fully explored. L001 needs new mechanism ideas.
**Next actions**:
- Probe shadow x pv_corr interaction (not Amihud)
- Probe shadow x volume competition conditioning

### Thesis Update
shadow x amount_Amihud is not a new mechanism — it is the same expression as F002 (shadow x volume-based Amihud, admitted batch_003). C004 is a pure duplicate.

### Evidence
- **支持**: F002 admit: alpha_surv=0.377, Barra_res=-0.176, shadow confirmed viable
- **反对**: C004 identical expression to F002 — confirmed duplicate

### Failure Boundary
shadow x Amihud (F002) already admitted. shadow x amount variant is same expression. Do not retry shadow x Amihud variants — they are fully explored.

### Open Questions
1. What shadow mechanism can work WITHOUT Amihud as conditioning partner?
2. Can shadow be combined with vol-competition or price-dynamics conditioning?

### Next Probes
- `Mul(ShadowRatio,Corr($close,$amount,20))` — shadow x amount correlation
- `Mul(ShadowRatio,Div(CsRank($turnover_rate),CsRank($volume)))` — shadow x volume competition
"""

write_reflection_md(Path('storage/logic/reflections/L004.md'), delta_l004, narrative_l004)
write_reflection_md(Path('storage/logic/reflections/L001.md'), delta_l001, narrative_l001)
print('Reflections written')

esc = GlobalEscalationDelta(
    batch_id='batch_041',
    status='applied',
    proposed_lessons=[],
    proposed_forbidden=[],
    logic_proposals=[],
    saturation_signal=None
)
save_global_escalation(Path('storage/state/global_escalation.yaml'), esc)
print('Global escalation saved')

from research.logic.reflect import recompute_research_state
recompute_research_state(Path('storage/logic/cards'), Path('storage/state/research_state.yaml'))
print('State recomputed')
print('Reflect complete')
