"""Sleep engine. NASA risk: Inadequate Sleep and Irregular Schedules.
Sleep never produces RED on its own: it is context that explains a complaint and changes tomorrow."""
from statistics import mean


def sleep_status(nights, R):
    """nights = last 7 sleep durations in hours, newest LAST. Returns status + the numbers behind it."""
    last = nights[-1]
    avg48 = round(mean(nights[-2:]), 1)
    avg7 = round(mean(nights), 1)
    debt7 = round(sum(max(0, R["sleep_goal_h"] - h) for h in nights), 1)   # hours owed this week

    if avg48 < R["sleep_very_low_48h"] or debt7 >= R["debt_high_h"]:
        status = "LOW"
    elif last < R["sleep_low_h"] or debt7 >= R["debt_mid_h"]:
        status = "WATCH"
    else:
        status = "OK"
    return {"status": status, "last": last, "avg48": avg48, "avg7": avg7, "debt7": debt7}
