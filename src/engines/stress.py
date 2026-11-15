"""Stress engine. NASA risk: Behavioral Changes and Psychiatric Disorders.
No device measures stress directly, so we use the astronaut's own rating plus one supporting signal (resting pulse).
This engine NEVER diagnoses. It notices a pattern and suggests a simple step."""


def stress_status(self_stress, resting_hr, base_hr_mean, recent_stress, R):
    """recent_stress = self ratings of the previous days, newest LAST."""
    high = self_stress >= R["stress_high"]
    supported = self_stress >= R["stress_mid"] and resting_hr >= base_hr_mean + R["hr_plus_for_stress"]

    n = R["stress_days_persistent"]
    previous = recent_stress[-(n - 1):] if n > 1 else []
    persistent = (high or supported) and len(previous) == n - 1 and all(s >= R["stress_high"] for s in previous)

    if persistent:
        status = "PERSISTENT"
    elif high or supported:
        status = "HIGH"
    else:
        status = "OK"
    return {"status": status, "self": self_stress, "hr_over_baseline": round(resting_hr - base_hr_mean)}
