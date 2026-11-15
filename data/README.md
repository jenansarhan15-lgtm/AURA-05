# Data inventory and sharing policy

The actual application data files are under `src/data/`, preserving the inherited import paths:

- `mission_simulated.csv`: synthetic demonstration records for four fictional crew IDs over 180 mission days.
- `generate_data.py`: generates demonstration records; run from `src/data/` if regeneration is needed.
- `rules.json`: prototype numeric settings.
- `knowledge.json`: symptom questions, first-aid summaries and inherited source labels.
- `support.json`: sleep, psychological-support and planning prompts.

No NASA astronaut-level health dataset is included. No live SQLite database, check-in history, session log or entered medical record is bundled. Running the app creates a new database locally; keep that generated database out of Git.

The root folder `data/` documents the dataset; it is not a second copy. Do not upload real health records, identifiable participants, exported SOS summaries or browser-session data.
