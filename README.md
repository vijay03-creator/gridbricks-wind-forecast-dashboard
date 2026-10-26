UK Wind Forecast Accuracy Dashboard

A decision-support dashboard for evaluating how accurately UK wind generation forecasts matched actual generation during January 2026. Built to help electricity buyers and procurement analysts understand forecast errors using information that was available before the purchase decision cutoff.

Project Links

- Live Dashboard: https://gridbricks-wind-forecast-dashboard-henna.vercel.app
- Demo Video: https://youtu.be/VhhX9xMhTqk?si=GPA1TssfsytmZ_Mk
- GitHub Repository: https://github.com/vijay03-creator/gridbricks-wind-forecast-dashboard

«Note: The dashboard is deployed separately from the Python backend. Confirm that the deployed frontend can reach the configured backend before relying on live results.»

Overview

Electricity procurement decisions depend on forecasts available at a particular point in time. Evaluating a decision using forecasts published afterward can introduce look-ahead bias and overstate the accuracy of the information available to the buyer.

This project provides an interactive dashboard to compare actual UK wind generation with eligible forecasts for a selected date range and decision lead time.

The dashboard presents summary metrics, actual-versus-forecast charts, forecast-error visualizations, and data-coverage information.

Key Features

- Date-range selection: Review forecast accuracy over a selected period.
- Decision lead-time selection: Evaluate forecasts using a configurable lead time before delivery.
- Forecast-versus-actual comparison: Visualize actual and forecast wind generation.
- Forecast-error analysis: Identify periods of over-forecasting and under-forecasting.
- Performance metrics: Review MAE, RMSE, forecast bias, and MAPE where applicable.
- Data coverage: Display the number of evaluated intervals relative to the expected intervals.
- API endpoints: Access configuration, metrics, time-series data, and a health check through the backend.
- Error handling: The application includes loading, error, and empty-state handling as described in the implementation.

Technology Stack

Frontend

- React
- Vite
- Tailwind CSS
- Recharts
- JavaScript

Backend

- Python
- FastAPI
- pandas

Data Source

- Elexon BMRS Insights API
- "FUELHH" — actual generation data
- "WINDFOR" — wind generation forecast data

Deployment and Development

- Vercel frontend configuration
- Docker and Docker Compose configuration
- Pytest and frontend tests

The actual availability of the backend, live upstream data, and Docker deployment depends on the environment and should be verified separately.

Data and Evaluation Methodology

Analysis Period

The dashboard is designed to analyze UK wind generation during 1–31 January 2026, with timestamps handled in UTC.

Avoiding Forecast Leakage

A central requirement is to use only forecasts that would have been available before the relevant purchase decision.

For a delivery interval starting at time "T" and a selected decision lead time "H", the forecast publication time must satisfy:

"forecast_publish_time <= T - H"

Among eligible forecasts, the application selects the latest forecast published before or at the cutoff.

Forecasts published after the cutoff must not be used in the evaluation because they were not available at the decision time.

Matching Forecasts and Actuals

Forecast and actual generation observations must be aligned to comparable delivery intervals before calculating errors.

Intervals without usable actual or eligible forecast data should not be treated as valid forecast comparisons. The evaluated-interval count helps make data coverage visible.

The implementation matches forecast and actual observations using delivery-interval timestamps. If upstream forecast data uses a different time resolution, this matching behavior and its effect on coverage should be verified against the live data.

Performance Metrics

Mean Absolute Error (MAE)

The average absolute difference between forecast and actual generation, measured in MW.

Lower MAE indicates smaller average forecast errors.

Root Mean Squared Error (RMSE)

The square root of the average squared forecast error. Because errors are squared before averaging, larger errors receive greater weight.

Forecast Bias

Bias is calculated using:

"forecast - actual"

- Positive bias indicates over-forecasting.
- Negative bias indicates under-forecasting.
- Bias near zero indicates little net directional error, though individual errors may still be large.

Mean Absolute Percentage Error (MAPE)

MAPE expresses absolute forecast error as a percentage of actual generation.

The implementation uses an actual-generation threshold of at least 100 MW when calculating MAPE to avoid unstable percentages when actual generation is close to zero. The displayed MAPE should therefore be interpreted alongside the number of eligible intervals.

Evaluated Intervals

The dashboard reports how many delivery intervals were evaluated compared with the expected interval count. Missing observations can reduce coverage and should be considered when interpreting the metrics.

Application Architecture

The application separates the user interface from data retrieval and processing.

User
 |
 v
React + Vite Dashboard
 |
 | HTTP requests
 v
FastAPI Backend
 |
 +--> Elexon BMRS API
 |
 +--> Forecast and actual data processing
 |
 +--> Decision-cutoff filtering
 |
 +--> Interval alignment
 |
 +--> Metric calculation
 |
 v
JSON Responses
 |
 v
Dashboard Charts and KPI Cards

Frontend Responsibilities

The frontend provides the interactive dashboard, date and lead-time controls, metric cards, charts, and user-facing loading, error, and empty states.

Backend Responsibilities

The backend retrieves and processes the relevant data, applies forecast eligibility rules, aligns forecast and actual observations, and calculates the evaluation metrics.

API Endpoints

The FastAPI backend documents the following endpoints:

Method| Endpoint| Purpose
GET| "/health"| Health check
GET| "/api/config"| Dashboard configuration and supported parameters
GET| "/api/metrics"| Summary metrics for the selected period and lead time
GET| "/api/series"| Time-series data for charts and interval-level analysis

Interactive API documentation is available locally at:

"http://127.0.0.1:8000/docs"

This local URL is for development. A publicly accessible API documentation URL is available only if the backend is deployed and exposed.

Local Development

Prerequisites

- Python
- Node.js and npm
- Git

1. Clone the repository

git clone https://github.com/vijay03-creator/gridbricks-wind-forecast-dashboard.git
cd gridbricks-wind-forecast-dashboard

2. Configure the backend

Open the backend directory:

cd backend

Create and activate a virtual environment.

Windows:

python -m venv .venv
.venv\Scripts\activate

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

Install dependencies using the dependency file present in the backend directory. For example, if the repository contains "requirements.txt":

pip install -r requirements.txt

Configure any required environment variables using the repository's ".env.example" file, if applicable.

Start the backend using the project's configured FastAPI entry point. For example, if the entry point is "main.py":

uvicorn main:app --reload --host 127.0.0.1 --port 8000

If your actual entry point or dependency filename differs, use the one provided in the repository.

3. Configure the frontend

Open a second terminal from the repository root:

cd frontend
npm install

Configure the frontend API base URL to point to the running backend, following the variable name documented in the frontend configuration or ".env.example".

Start the frontend:

npm run dev

Open the local URL printed by Vite, typically:

"http://localhost:5173"

4. Verify the backend

Open:

"http://127.0.0.1:8000/docs"

Check the available endpoints and verify that the frontend can successfully request data from the backend.

Testing

The repository includes backend and frontend test configurations.

Run the backend tests using the project's documented test command. If pytest is configured:

pytest

Run frontend tests using the test script defined in "frontend/package.json", for example:

npm test

Build the frontend for production using:

npm run build

Use the exact commands defined by the current repository if its scripts differ.

Verification note: A configured test suite does not itself prove that tests pass in every environment. Likewise, a successful frontend build does not prove that live API data or the deployed frontend-to-backend connection works. Verify these separately before claiming they are working.

Docker

The repository includes Docker-related configuration for containerized development or deployment.

Before relying on it, verify that the Dockerfiles and Compose configuration match the current project structure and required environment variables.

If Docker is available, run the repository's configured Compose command from the directory containing "docker-compose.yml":

docker compose up --build

Docker image builds and container startup should be confirmed in the target environment before being described as verified.

Deployment

Frontend

The frontend is intended to be hosted on Vercel.

Primary deployment URL:

https://gridbricks-wind-forecast-dashboard-henna.vercel.app

Backend

The Python backend requires a separately running and reachable service unless the deployment architecture has been changed to host it another way.

Configure the frontend to use the correct deployed backend URL. Verify the health endpoint, API responses, CORS configuration, and live dashboard behavior after deployment.

Deployment Checklist

- Confirm the frontend loads successfully.
- Confirm API requests reach the correct backend.
- Confirm live data is returned rather than placeholder or sample data.
- Confirm date and lead-time controls update the results.
- Confirm missing-data and upstream-error states behave correctly.
- Check logs for failed requests and configuration errors.

Limitations and Considerations

- Live data verification: Upstream API access and data availability must be verified in the deployed environment.
- Forecast resolution: Forecast and actual delivery intervals must be aligned correctly. Differences in time resolution can affect evaluation coverage.
- Missing observations: Metrics may be based on fewer intervals than the full expected period.
- Decision cutoff: Results depend on the chosen lead time and the correctness of publication timestamps.
- MAPE threshold: MAPE is calculated only for intervals meeting the actual-generation threshold, so its coverage may differ from other metrics.
- Historical scope: The dashboard evaluates a selected historical period; it is not a real-time trading or procurement execution system.
- Deployment dependencies: Frontend availability does not guarantee backend availability.

AI Assistance and Attribution

AI assistance was used during development to help generate and review portions of the code, tests, and documentation. The implementation should be reviewed and verified by the author, especially forecast cutoff logic, data alignment, metric calculations, and deployment behavior.

The upstream data source is Elexon BMRS Insights API. Please follow its applicable data-use terms and attribution requirements.

Author

Vijay Maddanimath

- GitHub: https://github.com/vijay03-creator
- Project repository: https://github.com/vijay03-creator/gridbricks-wind-forecast-dashboard

---

This project was developed as an energy forecast accuracy and procurement decision-support dashboard for the Gridbricks assignment.
