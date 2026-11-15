# AURA-05 — The Fifth Crew Member

**NOVARAIA-X | NASA Space Apps Challenge 2026**

**Challenge:** Create Health Monitoring Software for Astronauts on Space Missions

## Project Overview

AURA-05 is a bilingual astronaut-health support prototype designed to demonstrate how structured health observations, personal baselines, symptom checklists, sleep monitoring, and psychological-support prompts can assist crew members during long-duration space missions.

The system combines synthetic vital-sign measurements, personal health baselines, rule-based risk indicators, and follow-up workflows in one interface. It also includes a browser-based attention task and a simulated communication-delay mode.

AURA-05 explores how astronauts could organize health observations and follow-up activities when communication with Earth is delayed.

> **Important Disclaimer:** AURA-05 is a research and demonstration prototype. It is not a medical device, diagnostic system, or emergency service. It does not provide professional medical advice. All demonstration health measurements are synthetic. Do not enter real personal or health information. No NASA approval or endorsement is claimed.

## Live Application

**[Launch AURA-05](https://aegis-mind.replit.app/aura5/)**

**[GitHub Repository](https://github.com/jenansarhan15-lgtm/AURA-05)**

**Project Demo:** The presentation or demonstration link will be added here once publicly hosted.

## The Problem

Astronauts on long-duration missions may experience isolation, disrupted sleep, workload-related stress, and delays in communication with Earth.

Communication delays during Mars missions can make timely health observation and follow-up more challenging.

AURA-05 explores a crew-facing workflow for organizing health information, identifying unusual patterns, and supporting structured follow-up without claiming to replace medical professionals or autonomous mission medical systems.

## Key Features

- **Health Dashboard:** Displays six vital measurements with synthetic records and manual entries.
- **Personal Baselines:** Demonstrates baseline comparisons using four synthetic crew profiles across 180 mission days, with baselines derived from the first 14 days.
- **Daily Check-ins:** Morning and evening check-ins covering health, sleep, and stress.
- **Symptom Assessment:** Body-region selection, symptom questions, and rule-based urgency categories with explanations.
- **Follow-up Workflows:** Re-measurement guidance and first-aid reference information.
- **Attention Task:** A browser-based reaction-time task inspired by PVT-B research. It is not a validated PVT-B implementation.
- **Crew Readiness:** Demonstration of crew-readiness indicators, task-swap suggestions, and a next-day plan.
- **Silent Hour:** Simulates communication delays, records actions, and supports text-summary export.
- **Bilingual Interface:** English and Arabic interfaces, with browser-dependent speech recognition and speech synthesis.

## How to Try the Prototype

1. Open the live application.
2. Select a synthetic crew member and mission day.
3. Review the displayed measurements and personal-baseline comparisons.
4. Complete a morning or evening check-in using fictional values.
5. Select **I have a symptom**, choose a body region, and answer the symptom questions.
6. Review the explained urgency category and follow-up options.
7. Open **Silent Hour** to explore the simulated communication-delay workflow and export a summary.

### Data Labels

- **SIM:** Synthetic measurements.
- **MANUAL:** Values entered manually by the user.
- **REAL:** An actual browser attention-task session, not a real astronaut sensor measurement.

## Technology Stack

- Python
- Flask
- Jinja Templates
- SQLite
- HTML and CSS
- Vanilla JavaScript

## AI and Decision Methodology

AURA-05 uses explicit rules, personal-baseline comparisons, and structured decision logic to demonstrate health-monitoring workflows.

It does not use a trained neural network or an LLM as a clinical decision-maker. No trained model weights or model-accuracy claims are provided.

Replit Agent assisted with submission text, presentation copy, and repository packaging. The team should disclose any additional AI assistance used in the application, logo, images, or other project assets according to the competition's requirements.

For further details, see [AI Methodology](docs/AI_METHODOLOGY.md).

## NASA Resources and Research

NASA publications inform the prototype's design considerations, particularly communication latency, sleep and workload risks, and isolation-support needs.

No real astronaut health dataset is imported. All demonstration health measurements are synthetic.

The CSA Bio-Monitor is mentioned as a future wearable reference, not as a connected device.

For further details:

- [NASA and Research Sources](docs/NASA_DATA_SOURCES.md)
- [Dataset Notes](data/README.md)
- [Third-Party Notices](THIRD_PARTY_NOTICES.md)

## System Limitations

- No connected wearable or live astronaut sensor feed.
- No automatic SOS dispatch or real crew notification.
- No real mission-control communication.
- Communication-delay behavior is simulated.
- Some interface messages represent simulated notifications only.
- Medical thresholds and reference content require qualified professional review.
- NEWS2-derived bands do not establish full NEWS2 compliance.
- The prototype does not claim production-level security, access control, or privacy assurance.
- Browser speech services and external fonts may require an internet connection.
- Full offline operation is not guaranteed.

See [Testing and Limitations](docs/TESTING_AND_LIMITATIONS.md).

## Running Locally

**Requirements:** Python 3.11 or later.

```bash
python -m pip install -r requirements.txt
python src/main.py
```

Open the application at:

```text
http://localhost:5000
```

The application creates its SQLite database automatically using the included synthetic CSV data.

Run the engine checks with:

```bash
python tests/test_engines.py
```

This package uses Flask's development server and a per-process random session key. Sessions reset after restart. It is intended for local synthetic demonstrations, not production deployment.

## Repository Structure

```text
AURA-05/
├── README.md
├── requirements.txt
├── docs/
├── src/
│   └── data/
├── data/
├── models/
├── screenshots/
├── tests/
├── UPLOAD_CHECKLIST.md
└── THIRD_PARTY_NOTICES.md
```

## Team

**NOVARAIA-X**

| Member | Role |
|---|---|
| Jana mowafag mohmmad bni abdalhamed | Team Leader |
| Jenan Fuad Sarhan | Team Member |
| um kalthom abd alsalam | Team Member |
| Shaimaa abbas rababa | Team Member |

Individual technical responsibilities are not assigned here unless confirmed by the team.

## License and Third-Party Materials

No open-source license has been selected or granted by this package. Public availability on GitHub does not automatically grant permission to reuse the project.

The team should verify ownership and permissions for inherited code, logos, images, reference materials, and other third-party assets.

See [Third-Party Notices](THIRD_PARTY_NOTICES.md).
