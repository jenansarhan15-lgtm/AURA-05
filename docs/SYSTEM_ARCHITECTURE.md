# System architecture

```text
Browser: HTML/Jinja views + CSS + JavaScript
   | HTTP requests / session cookie
Flask routes: src/main.py
   | context, symptoms, check-ins, task results
Rule engines: src/engines/
   | baseline, triage, trends, sleep, stress, focus, readiness, planning
SQLite storage: src/storage.py -> src/data/aegis.db
   | initialized from synthetic CSV
Knowledge/configuration: src/data/*.json
```

The application renders templates on the Flask server. Browser JavaScript supports the body interaction, reaction-time task and browser speech APIs. SQLite stores synthetic records and any entered check-ins or session records on the machine running Flask.

The application has no trained-model inference service or actual wearable/mission-control integration. Silent Hour stores demonstration actions and generates an export; an export is not evidence of network delivery.

## Standalone packaging differences

The supplied application code is copied under `src/`, while tests live under `tests/` with their import path updated. The session key is generated per process instead of using the inherited fixed demo string. The storage description is corrected to distinguish server storage from device-only storage. Live databases, cached bytecode and a redundant CSV copy are excluded.

The Replit path-mounting wrapper is not needed for local root-path execution and is not included. No deployed website code is modified by this package.
