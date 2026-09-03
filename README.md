# PlacementOps

## Deterministic Placement Scheduling Engine

PlacementOps is a constraint-aware interview scheduling and deterministic replanning platform built for high-volume campus placement operations.

### Video Walkthrough

**Main project walkthrough:**  
https://youtu.be/PpCkmrgLxgI

The walkthrough demonstrates the PlacementOps workflow, scheduling engine, operations console, analytics, and disruption-aware replanning.

### Project Scale

| Metric | Value |
|---|---:|
| Students | 800 |
| Companies | 35 |
| Interview Panels | 85 |
| Rooms | 20 |
| Interview Requests | 859 |
| Placement Days | 4 |
| Scheduled Interviews | 476 |
| Unscheduled Interviews | 383 |
| Completion Rate | 55.41% |
| Scheduler Runtime | ~130 ms |
| Scheduling Conflicts | 0 |

### What Makes PlacementOps Interesting

- **Constraint-aware scheduling** — handles room, panel, student, company, availability, and operating-hour constraints.
- **Deterministic execution** — the same input produces the same schedule.
- **Deterministic replanning** — disruptions are handled without rebuilding the system around random decisions.
- **Performance-focused engine** — optimized using resource indexes, incremental state, pruning, and short-circuit validation.
- **Operations-focused interface** — provides a practical console for monitoring and managing placement activity.

---

## The Problem

Campus placement interview scheduling is a constrained resource-allocation problem.

A realistic schedule must coordinate:

- Student availability
- Company interview requirements
- Interview panel availability
- Room availability
- Daily operating hours
- Student daily interview limits
- Panel daily interview limits
- Company scheduling limits
- Existing assignments
- Disruptions that occur after scheduling

The problem becomes more difficult when a schedule is already active and something changes.

Examples include:

- A room becoming unavailable
- A panel dropping out
- A company being delayed
- A student withdrawing

A useful system therefore needs to do more than generate an initial timetable. It must also **recover from operational disruptions while preserving unaffected work**.

---

## The Solution

PlacementOps treats scheduling as an operational loop:

1. Generate an initial schedule.
2. Validate the schedule against hard constraints.
3. Detect and process disruptions.
4. Replan affected work deterministically.
5. Preserve unaffected assignments whenever possible.
6. Expose the resulting state through an operations console.
7. Provide analytics and AI-assisted interpretation.

The result is a system that combines a deterministic scheduling engine with a practical operations layer.

---

## Key Capabilities

### Schedule Generation

- High-volume interview scheduling
- Deterministic candidate generation
- Hard constraint validation
- Resource-aware assignment
- Deterministic tie-breaking
- Explicit unscheduled outcomes

### Disruption & Replanning

Supported disruption categories include:

- `ROOM_UNAVAILABLE`
- `PANEL_UNAVAILABLE`
- `COMPANY_DELAY`
- `STUDENT_WITHDRAWAL`

Replanning:

1. Identifies affected assignments.
2. Removes or adjusts impacted work.
3. Preserves unaffected assignments.
4. Searches for feasible alternatives.
5. Validates the final schedule.
6. Reports what changed.

### Schedule Exploration

The frontend provides:

- Schedule overview
- Day-based schedule exploration
- Timeline visualization
- Assignment details
- Unscheduled interview inspection
- Replanning controls
- Operational notifications

### Analytics

The console surfaces scheduling and capacity information so operators can understand:

- Scheduling completion
- Resource utilization
- Company distribution
- Panel workload
- Room workload
- Unscheduled demand
- Replanning impact

### AI Assistance

PlacementOps also includes a Gemini-powered assistant that can answer questions about the current placement state while keeping deterministic scheduling logic separate from AI interpretation.

---

## System Architecture

```text
                         PlacementOps
                              |
                +-------------+-------------+
                |                           |
          React Operations UI          AI Assistant
                |                           |
                |                      Gemini API
                |                           |
                +-------------+-------------+
                              |
                           FastAPI
                              |
             +----------------+----------------+
             |                                 |
       Scheduling Engine                 Replanning Engine
             |                                 |
             +----------------+----------------+
                              |
                        Placement Data
          Students | Companies | Panels | Rooms
                    Interviews | Availability
```

### Architecture Boundaries

**Frontend**

Responsible for:

- Operational visualization
- User interactions
- Schedule exploration
- Replanning controls
- Analytics presentation
- Assistant interaction

**Backend**

Responsible for:

- API validation
- Scheduling
- Replanning
- Schedule integrity
- Analytics data
- AI orchestration

**Scheduling Engine**

Responsible for deterministic assignment decisions and constraint enforcement.

**AI Assistant**

Responsible for natural-language interpretation and explanation. It does not replace the deterministic scheduling engine.

---

## Scheduling Engine

PlacementOps uses a deterministic heuristic scheduling strategy.

### 1. Candidate Generation

The engine evaluates possible combinations of:

- Day
- Time slot
- Panel
- Room

for each interview request.

### 2. Hard Constraints

Candidates are rejected when they violate constraints such as:

- Student conflicts
- Panel conflicts
- Room conflicts
- Availability restrictions
- Operating hours
- Daily resource limits
- Existing schedule assignments

### 3. Scoring

Feasible candidates are ranked using deterministic scheduling preferences.

### 4. Tie-Breaking

Stable ordering ensures reproducible results when multiple candidates have equivalent scores.

### 5. Incremental State

The optimized implementation maintains scheduling state incrementally rather than repeatedly scanning the complete schedule.

This includes:

- Resource occupancy indexes
- Student/company/panel/room daily counts
- Precomputed static availability
- Hierarchical pruning
- Short-circuit constraint validation
- On-demand best-candidate selection

### Determinism

The optimization was designed to preserve the original scheduler's behavior.

For the canonical dataset:

- All **476 assignment tuples** matched the reference implementation.
- The unscheduled interview ID sequence matched exactly.
- **96,421 / 96,421** candidate scores matched.

This means the performance improvements changed the implementation strategy without changing scheduling behavior.

---

## Replanning & Disruption Recovery

Replanning is treated as a first-class scheduling operation.

### Workflow

```text
Existing Schedule
       |
       v
Disruption Detected
       |
       v
Identify Affected Assignments
       |
       v
Remove / Adjust Impacted Work
       |
       v
Find Feasible Alternatives
       |
       v
Validate Final Schedule
       |
       v
Return Replanned Schedule
```

The replanning process is designed to minimize unnecessary changes.

### Student Withdrawal Example

For the canonical end-to-end withdrawal scenario:

- Baseline scheduled: **476**
- Replanned scheduled: **473**
- Affected assignments: **3**
- Remaining assignments for withdrawn student: **0**
- Newly unscheduled interviews: **3**

The final schedule is validated for assignment integrity, conflicts, accounting, and disruption postconditions.

---

## Data Model & Dataset

The canonical seed is:

```text
20260829
```

It contains:

- **800 students**
- **35 companies**
- **85 panels**
- **20 rooms**
- **859 interview requests**
- **4 placement days**

Baseline scheduling produced:

- **476 scheduled**
- **383 unscheduled**
- **55.41% completion**
- **0 conflicts**

The generated dataset is designed to create meaningful resource pressure rather than producing an unrealistically easy schedule.

---

## API Design

The backend exposes the following primary endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/schedule/generate` | Generate a schedule |
| POST | `/schedule/replan` | Replan after a disruption |
| POST | `/assistant/query` | Ask the AI assistant |
| POST | `/assistant/stream` | Stream assistant responses |

FastAPI also exposes interactive API documentation at:

```text
/docs
```

### Validation

The API distinguishes between:

- Malformed request validation
- Domain-level scheduling/replanning validation

Invalid payloads are rejected rather than silently producing an incorrect schedule.

---

## Performance Engineering

The scheduler was optimized after profiling the original implementation.

### Original Hotspots

Profiling identified expensive repeated work in:

- Existing conflict checks
- Time-overlap checks
- Candidate generation
- Repeated scoring scans
- Eager evaluation of all resource combinations

The original benchmark was approximately:

- **72.85M function calls**
- **~33.7 seconds**

### Optimization Strategy

The optimized implementation introduced:

1. O(1) resource occupancy indexes.
2. Incremental daily counters.
3. Precomputed availability.
4. Hierarchical safe pruning.
5. Sequential short-circuit validation.
6. On-demand best-candidate selection.

### Benchmark

Five optimized benchmark runs:

```text
0.1275 s
0.1289 s
0.1306 s
0.1307 s
0.1338 s
```

Median:

```text
~0.1306 seconds
```

This represents more than a **99% reduction** versus the earlier benchmark under the corresponding benchmark setup, while preserving exact canonical scheduling behavior.

---

## Correctness, Testing & Validation

The project includes automated tests covering:

- Scheduling constraints
- Schedule integrity
- Conflict detection
- Deterministic scheduling
- Replanning validation
- Disruption postconditions
- API validation
- End-to-end withdrawal behavior
- Resource availability handling

Latest known test suite:

```text
57 tests
55 passed
2 skipped
```

Additional validation confirmed:

- 0 scheduling conflicts
- 476 / 476 canonical assignments valid
- Exact assignment equivalence after optimization
- Dataset integrity preserved
- No global mutable scheduler state
- Student occupancy enforced across companies

---

## Frontend & Operations Console

The PlacementOps frontend is designed as an operations console rather than a simple form-based demo.

### Main Areas

- **Overview** — high-level placement metrics
- **Schedule Explorer** — inspect scheduled interviews
- **Timeline** — visualize daily interview activity
- **Analytics** — understand demand and resource usage
- **Replanning** — trigger disruption workflows
- **Unscheduled** — inspect unresolved interview demand
- **Assignment Details** — inspect individual assignments
- **Notifications** — surface operational events

The interface uses a **Midnight Cobalt + Ice** visual system and includes responsive navigation for different screen sizes.

---

## AI Assistant & Gemini Integration

The assistant uses Google Gemini as an interpretation layer around deterministic PlacementOps data.

The backend provides structured context to the model so that responses can reference operational facts such as schedule state and resource information.

### Design Principles

- Scheduling remains deterministic.
- AI does not directly modify scheduling state.
- Gemini credentials remain server-side.
- Streaming responses use Server-Sent Events.
- Assistant failures are isolated from the core scheduling engine.

This separation keeps AI useful for natural-language interaction without making the core scheduling system dependent on probabilistic model output.

---

## Project Structure

```text
placement-ops/
├── backend/
│   └── placementops/
│       ├── app.py
│       ├── assistant/
│       ├── scheduling/
│       ├── models/
│       └── ...
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Technology Stack

### Frontend

- React 19
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Uvicorn

### AI

- Google Gemini

### Testing & Engineering

- Python `unittest`
- Git
- GitHub

---

## Local Development & Setup

### Prerequisites

- Python 3.x
- Node.js
- npm

### Backend

From the repository root:

```bash
python -m uvicorn placementops.app:app --reload --app-dir backend
```

The backend runs locally on:

```text
http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` requests to the local FastAPI backend.

### Environment Variables

Create the backend environment configuration using:

```text
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Never commit real credentials to Git.

### Tests

From the repository root:

```powershell
$env:PYTHONPATH="backend"
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## API Usage & Example Workflow

### Generate a Schedule

```http
POST /schedule/generate
```

The endpoint generates a deterministic schedule from the supplied placement data.

### Replan a Schedule

```http
POST /schedule/replan
```

The request includes the current schedule and disruption information. The backend identifies affected assignments, replans where possible, and validates the final result.

### Ask the Assistant

```http
POST /assistant/query
```

For streaming interaction:

```http
POST /assistant/stream
```

The frontend consumes the assistant response through the API layer.

---

## Deployment & Production Configuration

### Frontend

The frontend can be deployed to Vercel with:

```text
Root Directory: frontend
```

### Backend

The FastAPI backend can be deployed to Render.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn placementops.app:app --host 0.0.0.0 --port $PORT --app-dir backend
```

Production environment variables include:

```text
GEMINI_API_KEY
GEMINI_MODEL
```

The deployed frontend should be configured to communicate with the deployed backend API.

---

## Future Improvements

Potential extensions include:

- More advanced optimization algorithms
- Larger-scale stress testing
- Additional disruption types
- Richer operational analytics
- Authentication and role-based access
- Persistent schedule storage
- Audit logs
- More sophisticated AI-assisted reporting

These are future improvements rather than requirements for the current deterministic scheduling workflow.

---

## Project Links

### Video Walkthrough

https://youtu.be/PpCkmrgLxgI

### Live Demo

https://placement-ops-final-qxu31vmcd-yashsharma23csds-2811s-projects.vercel.app/

### GitHub

https://github.com/ys18yash/placement-ops

### API Documentation

Available through the deployed backend's `/docs` endpoint.

---

## License

This project is intended as a technical assessment and portfolio project.

---

## Author

**Yash Sharma**

Software Engineering | Full-Stack Development | Backend | AI Integration
