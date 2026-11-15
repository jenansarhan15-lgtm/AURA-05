# Testing and limitations

## Reproduce the checks

```sh
python -m pip install -r requirements.txt
python tests/test_engines.py
```

Run on a fresh copy, without an existing database. The inherited checks load the synthetic mission, exercise selected urgency cases and attention scoring, and inspect resting categories. They are assertions, not a comprehensive clinical test suite.

The package is checked with these assertions and Flask's test client for read-only page rendering. See `VERIFICATION.md` at repository root for actual results. No browser automation, wearable hardware test, medical evaluation, authentication audit or independent security audit is implied.

## Known boundaries

- No trained model, clinical accuracy measurement, clinical approval or proven benefit.
- Some messaging describes simulated notices as sent. There is no working ground-delivery channel or emergency dispatch.
- Rule paths and contextual modifiers need further review for cases that could understate vital-sign risk.
- Only synthetic data are suitable for this public prototype.
- Hosted storage is on the application server. User-level access separation, production security and privacy controls need work.
- Default development serving and per-process session keys are not production architecture.
- Speech recognition can rely on browser/vendor network services; Google Fonts is external.
- Synthetic records cannot demonstrate generalization to real astronauts.
- Configurable thresholds, first aid and advice require qualified clinical and operational review.

Do not use the system for real symptoms or emergencies.
