# PlacementOps

## Constraint-Aware Placement Interview Scheduling & Replanning Platform

PlacementOps is a full-stack placement operations platform for generating, validating, monitoring, and replanning college placement interview schedules.

The system is designed around a realistic placement environment where multiple students, companies, interview panels, rooms, interview slots, and operational constraints must be coordinated simultaneously.

PlacementOps provides a scheduling backend and a web-based operations dashboard that allows placement teams to generate schedules, inspect their validity and utilization, track unscheduled interviews, and replan schedules when operational disruptions occur.

> **Project Status: 100% Completed**

---

# 1. Project Overview

Managing placement interviews manually becomes difficult when many interviews must be coordinated across limited rooms, panels, companies, students, days, and time slots.

A change to one resource can also affect several other interviews.

For example:

- A room may become unavailable.
- An interview panel may drop out.
- A company may be delayed.
- A student may withdraw.

PlacementOps addresses this problem through a constraint-aware scheduling and replanning workflow.

The platform provides:

1. Deterministic schedule generation
2. Schedule validation
3. Interview assignment management
4. Resource utilization metrics
5. Unscheduled interview tracking
6. Disruption-aware replanning
7. A web dashboard for placement operations

---

# 2. Project Status

**100% Completed**

The complete PlacementOps application has been implemented with:

- Backend scheduling APIs
- Schedule generation
- Schedule validation
- Schedule replanning
- Disruption handling
- Resource utilization metrics
- Unscheduled interview tracking
- React frontend dashboard
- Frontend/backend integration
- Production frontend build configuration
- Project documentation

The backend APIs were manually verified during development, including the health check, schedule generation, and schedule replanning workflows.

---

# 3. Core Features

## 3.1 Schedule Generation

PlacementOps generates an interview schedule from the available placement data.

Generated assignments can contain:

- Interview ID
- Student ID
- Company ID
- Panel ID
- Room ID
- Interview day
- Start time
- End time

The generated schedule is returned together with validation information.

Example:

```json
{
  "validation": {
    "valid": true,
    "errors": []
  }
}
```

---

## 3.2 Constraint-Aware Scheduling

The scheduling engine works with available placement resources and scheduling constraints.

The system coordinates:

- Students
- Companies
- Interview panels
- Rooms
- Interview slots
- Placement days

The generated schedule is validated before being consumed by the frontend.

---

## 3.3 Schedule Validation

Every generated schedule is accompanied by validation information.

This provides an explicit indication of whether the generated schedule satisfies the required constraints.

Example:

```json
{
  "valid": true,
  "errors": []
}
```

This allows the system to distinguish between a valid generated schedule and a schedule containing constraint violations.

---

## 3.4 Disruption-Aware Replanning

Real placement operations are dynamic.

When a disruption occurs, an existing schedule may need to be updated while maintaining feasibility.

PlacementOps provides a dedicated replanning API.

Supported disruption scenarios include:

- Company delay
- Panel dropout
- Student withdrawal
- Room unavailability

The replanning workflow generates an updated schedule based on the disruption.

---

## 3.5 Resource Utilization

The dashboard provides operational visibility through resource utilization metrics.

The application tracks:

- Room utilization
- Panel utilization
- Completion rate
- Scheduled interviews
- Unscheduled interviews
- Schedule span

These metrics help placement administrators understand how effectively available resources are being used.

---

## 3.6 Unscheduled Interview Tracking

Interviews that cannot be assigned to a valid slot are tracked separately.

The dashboard exposes:

- Total interviews
- Scheduled interviews
- Unscheduled interviews
- Completion rate
- IDs of interviews requiring attention

This makes scheduling gaps visible instead of silently hiding them.

---

## 3.7 Schedule Overview

The frontend provides a schedule table containing:

| Field     | Description          |
| --------- | -------------------- |
| Interview | Interview identifier |
| Student   | Student identifier   |
| Company   | Company identifier   |
| Room      | Assigned room        |
| Day       | Placement day        |
| Time      | Interview time range |

The dashboard presents generated assignments in an easy-to-scan operational format.

---

# 4. Disruption Handling

PlacementOps supports four major operational disruption categories.

## Company Delay

A company may be delayed, requiring affected interviews to be reconsidered during replanning.

## Panel Dropout

An interview panel may become unavailable.

The replanning process accounts for the reduced panel availability when generating the updated schedule.

## Student Withdrawal

A student may withdraw from the placement process.

The system accounts for the student's interview during replanning.

## Room Unavailability

A room may become unavailable during the placement process.

The replanning API accepts the affected room and generates an updated schedule that accounts for the disruption.

Example request:

```json
{
  "seed": 20260829,
  "disruption": {
    "id": "TEST-ROOM",
    "type": "ROOM_UNAVAILABLE",
    "day": "DAY_4",
    "effective_time": null,
    "resource_id": "ROOM001",
    "details": "Test room outage"
  }
}
```

---

# 5. System Architecture

PlacementOps follows a frontend/backend architecture.

```text
                         PlacementOps
                              |
                +-------------+-------------+
                |                           |
                v                           v
        React Frontend              FastAPI Backend
                |                           |
                |       HTTP / JSON         |
                +------------->-------------+
                                            |
                                            v
                                  Scheduling Engine
                                            |
                         +------------------+------------------+
                         |                  |                  |
                         v                  v                  v
                    Generation         Validation         Replanning
```

### Frontend Responsibilities

The frontend handles:

- Dashboard rendering
- User interaction
- Schedule generation requests
- Schedule display
- Metrics display
- Resource utilization visualization
- Unscheduled interview visibility
- API error handling

### Backend Responsibilities

The backend handles:

- API endpoints
- Schedule generation
- Scheduling logic
- Schedule validation
- Disruption processing
- Schedule replanning
- Metrics generation

---

# 6. Technology Stack

## Frontend

- React 19
- React DOM
- Vite
- JavaScript
- CSS

## Backend

- Python
- FastAPI
- Uvicorn

## Testing & Development

- pytest
- ESLint
- npm
- pip
- Git
- GitHub

---

# 7. Project Structure

```text
placement-ops/
│
├── backend/
│   └── ...
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── dist/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── eslint.config.js
│
├── data/
│   └── ...
│
├── docs/
│   └── ...
│
├── scripts/
│   └── ...
│
├── tests/
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 8. Backend Setup

## Requirements

The backend requires:

- Python 3.x
- pip

Install dependencies from the project root:

```powershell
pip install -r requirements.txt
```

### Recommended Virtual Environment

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# 9. Start the Backend

From the project root:

```powershell
python -m uvicorn placementops.app:app --reload --host 127.0.0.1 --port 8000
```

The backend runs on:

```text
http://127.0.0.1:8000
```

---

# 10. Backend API

## Health Check

### Endpoint

```text
GET /health
```

PowerShell:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

The endpoint was manually verified during development with:

```text
HTTP 200 OK
```

---

# 11. Generate Schedule API

### Endpoint

```text
POST /schedule/generate
```

A seed can be supplied to make the scheduling run reproducible.

Example:

```powershell
Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -Uri "http://127.0.0.1:8000/schedule/generate?seed=20260829"
```

The API returns the generated schedule together with validation information and scheduling data.

Example response structure:

```json
{
  "seed": 20260829,
  "validation": {
    "valid": true,
    "errors": []
  },
  "schedule": {
    "assignments": [],
    "unscheduled_interview_ids": []
  }
}
```

---

# 12. Replanning API

### Endpoint

```text
POST /schedule/replan
```

The endpoint accepts a disruption together with the scheduling seed.

Example:

```powershell
$body = @{
    seed = 20260829
    disruption = @{
        id = "TEST-ROOM"
        type = "ROOM_UNAVAILABLE"
        day = "DAY_4"
        effective_time = $null
        resource_id = "ROOM001"
        details = "Test room outage"
    }
} | ConvertTo-Json -Depth 5

Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -Uri "http://127.0.0.1:8000/schedule/replan" `
  -ContentType "application/json" `
  -Body $body
```

The replanning API was manually verified during development with:

```text
HTTP 200 OK
```

---

# 13. Frontend Setup

Open a second terminal.

Navigate to the frontend:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Vite will display the local frontend URL in the terminal.

---

# 14. Frontend API Integration

The frontend communicates with the backend through the `/api` path.

The Vite development server is configured to proxy these requests to:

```text
http://127.0.0.1:8000
```

The frontend therefore calls:

```text
/api/schedule/generate
```

while Vite forwards the request to the backend scheduling endpoint.

This keeps frontend API calls clean during local development and avoids hard-coding the backend server into React components.

---

# 15. Frontend Commands

From the `frontend` directory:

### Development

```powershell
npm run dev
```

### Production Build

```powershell
npm run build
```

### Lint

```powershell
npm run lint
```

### Preview Production Build

```powershell
npm run preview
```

---

# 16. Complete Application Workflow

```text
                    Start Backend
                         |
                         v
                   Start Frontend
                         |
                         v
              Open PlacementOps
                    Dashboard
                         |
                         v
                Generate Schedule
                         |
                         v
                Scheduling Engine
                         |
                         v
                Validate Schedule
                         |
                         v
          Display Schedule + Metrics
                         |
                         v
               Operational Event
                         |
                         v
                Submit Disruption
                         |
                         v
                    Replanning
                         |
                         v
             Validate Updated Schedule
                         |
                         v
              Display Updated Result
```

---

# 17. Reproducibility

Schedule generation supports a seed.

For example:

```text
20260829
```

Using a fixed seed allows scheduling runs to be reproduced consistently.

This is useful for:

- Debugging
- Testing
- Comparing generated schedules
- Demonstrating the scheduling engine
- Reproducing scheduling scenarios

---

# 18. Validation & Verification

The application was manually verified through its backend APIs.

## Health Endpoint

```text
GET /health
```

Result:

```text
HTTP 200 OK
```

Response:

```json
{
  "status": "ok"
}
```

## Schedule Generation

```text
POST /schedule/generate
```

Result:

```text
HTTP 200 OK
```

The generated schedule returned successful validation:

```json
{
  "valid": true,
  "errors": []
}
```

## Schedule Replanning

```text
POST /schedule/replan
```

Result:

```text
HTTP 200 OK
```

A room-unavailability disruption was successfully submitted to the replanning API during manual verification.

---

# 19. Testing

Automated tests are located in:

```text
tests/
```

The project includes a testing setup using `pytest`.

Frontend linting can be run with:

```powershell
cd frontend
npm run lint
```

The frontend production build can be generated with:

```powershell
npm run build
```

> Automated tests were not used as the basis for the manual API verification claims above. The documented verification refers specifically to the backend API workflows that were manually executed during development.

---

# 20. Production Build

To generate the production frontend:

```powershell
cd frontend
npm run build
```

The generated production files are placed in:

```text
frontend/dist/
```

---

# 21. Engineering Principles

PlacementOps was developed around several core engineering principles.

### Determinism

A scheduling seed makes scheduling behavior reproducible.

### Constraint Awareness

Scheduling decisions consider available placement resources and constraints.

### Validation

Generated schedules are explicitly validated before being presented as valid.

### Resilience

The system supports replanning when operational conditions change.

### Operational Visibility

Important scheduling metrics are exposed through the dashboard.

### Separation of Concerns

The React frontend handles presentation and interaction while the backend owns scheduling and replanning logic.

---

# 22. Dashboard

The PlacementOps dashboard provides an operational view of the generated schedule.

It includes:

## Header

Displays:

- PlacementOps branding
- Scheduling platform description
- API connection status

## Schedule Generation

A dedicated action allows the operator to generate the schedule.

## Metrics

The dashboard displays:

- Total Interviews
- Scheduled
- Unscheduled
- Completion Rate

## Schedule Overview

Displays generated interview assignments.

## Resource Utilization

Displays:

- Room utilization
- Panel utilization

## Schedule Span

Displays scheduling duration across placement days.

## Needs Attention

Displays the number of interviews that require attention because they do not currently have a schedule slot.

---

# 23. API Response Design

The scheduling API returns structured JSON so that the frontend can consume scheduling results directly.

The response contains scheduling information such as:

```text
seed
validation
schedule
assignments
unscheduled_interview_ids
metrics
```

This separation allows the scheduling engine to remain independent from the presentation layer.

---

# 24. Error Handling

The frontend handles unsuccessful API responses and displays an error banner when schedule generation fails.

The UI also provides loading feedback while the scheduling request is being processed.

This prevents duplicate generation requests and gives the operator immediate feedback about the API operation.

---

# 25. Project Completion

PlacementOps is **100% completed**.

The final application includes the complete intended workflow:

```text
Input Placement Data
        ↓
Schedule Generation
        ↓
Schedule Validation
        ↓
Operational Metrics
        ↓
Dashboard Visualization
        ↓
Disruption Handling
        ↓
Schedule Replanning
        ↓
Updated Schedule
```

The project provides a complete full-stack implementation for constraint-aware placement interview scheduling and operational replanning.
