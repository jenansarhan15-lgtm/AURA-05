# Adaptive monitoring logic

1. Load a synthetic crew member and mission day.
2. Build a personal reference from the first 14 days.
3. Prefer manual vital entries when present; otherwise display synthetic measurements.
4. Compare recent observations against baseline and configured thresholds.
5. Combine symptom/danger responses and vital measurements using explicit rules.
6. Include sleep, stress and attention indicators in prototype follow-up suggestions.
7. Present an explained urgency category and re-measurement guidance.

Settings are primarily collected in `src/data/rules.json`; symptom material and support prompts are in the other JSON files.

The intended safety principle is that contextual factors must not lower danger-sign or vital-sign risk. That principle is **not a clinical validation result**. Some inherited implementation paths require further safety review; the current implementation must not be used to decide real medical care.

The green/yellow/strong-yellow/red categories are prototype outputs, not probabilities or calibrated diagnoses. “Adaptive” refers to baseline comparisons and context-dependent rules—not model training, online learning or automatic changes to spacecraft operations.
