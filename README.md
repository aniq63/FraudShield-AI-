<div align="center">
  <h1>FraudShield AI</h1>
  <p>Real-time fraud detection with machine learning, streaming inference, and LLM explanations.</p>
  <p>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11 or newer"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
    <a href="https://mlflow.org/"><img src="https://img.shields.io/badge/MLflow-model%20tracking-0194E2?logo=mlflow&logoColor=white" alt="MLflow"></a>
  </p>
</div>

FraudShield AI processes simulated financial transactions through a trained fraud model, streams results to a browser dashboard, and generates an explanation for blocked transactions through Groq and LangChain.

## What It Does

- Loads sampled train and test data from `datasource/`.
- Cleans and standardizes the source schema.
- Builds distance, log-amount, transaction-hour, buyer-age, and night-transaction features.
- Trains Logistic Regression, Decision Tree, Random Forest, and XGBoost candidates.
- Selects the best candidate by recall and logs its model and preprocessor to MLflow.
- Registers the candidate and promotes it through Staging and Production when its recall improves.
- Loads the Production model at API startup.
- Processes transactions through an in-memory queue and background consumer.
- Sends completed predictions to browser clients with Server-Sent Events.
- Calls the configured Groq model for blocked-transaction reasoning.

## Architecture

```text
CSV data
   |
   v
Ingestion -> Transformation -> Feature engineering -> Preparation
                                                        |
                                                        v
                                  Model training -> MLflow/DagsHub registry
                                                        |
                                                        v
Browser -> FastAPI -> Transaction generator -> Queue -> Consumer
                                                       |       |
                                                       |       +-> Groq/LangChain reasoning
                                                       +----------> Prediction and SSE result
```

The application stores the latest results in a thread-safe in-memory deque with a maximum of 5,000 entries. Results are lost when the process restarts.

## Repository Layout

```text
.
├── api/
│   └── routes.py                         FastAPI routes and in-memory result store
├── datasource/
│   ├── train_sampled.csv                Training data
│   └── test_sampled.csv                 Evaluation data
├── frontend/
│   ├── dashboard.html                    Static monitoring dashboard
│   ├── index.html                        Static project page
│   └── simulator.html                    Static transaction simulator
├── frontend-react/                       Vite and React frontend
├── src/
│   ├── components/                       ETL, preparation, training, evaluation, registry
│   ├── inference/                        ML prediction and LLM reasoning
│   ├── pipelines/                        Training and streaming pipelines
│   └── simulator/                        Historical transaction generator
├── tests/                                Pytest suite
├── main.py                               FastAPI and Uvicorn entry point
├── requirements.txt                      Python dependencies
└── .github/workflows/ci.yml              GitHub Actions test workflow
```

## Requirements

- Python 3.11 or newer is used by CI.
- A Groq API key for LLM reasoning.
- A DagsHub or compatible MLflow tracking account for training and model loading.
- Node.js and npm only if using `frontend-react/`.

## Installation

Create and activate a virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env_example` to `.env` and replace the placeholder values:

```powershell
Copy-Item .env_example .env
```

Required for the default configuration:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=openai/gpt-oss-20b
MLFLOW_TRACKING_USERNAME=your_dagshub_username
MLFLOW_TRACKING_PASSWORD=your_dagshub_token
```

Optional variables:

```dotenv
DAGSHUB_REPO_OWNER=aniqramzan5758
DAGSHUB_REPO_NAME=FraudShield-AI-
MLFLOW_TRACKING_URI=https://dagshub.com/aniqramzan5758/FraudShield-AI-.mlflow
HOST=0.0.0.0
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=*
```

`MLFLOW_TRACKING_PASSWORD` may also be supplied as `DAGSHUB_TOKEN`. Never commit `.env` or expose API keys in frontend code.

## Run the Backend

From the repository root:

```powershell
python main.py
```

The API listens at `http://127.0.0.1:8000`. Startup loads the Production model and its matching preprocessor before the server reports readiness. The first startup can take several seconds because artifacts are downloaded from MLflow/DagsHub.

Interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Run the Frontend

### Static frontend

Open `frontend/simulator.html` or `frontend/dashboard.html` in a browser after starting the backend. When opened locally, these pages use `http://127.0.0.1:8000` automatically.

### React frontend

```powershell
cd frontend-react
npm install
npm run dev
```

For a production build:

```powershell
npm run build
npm run preview
```

The React client uses the same REST and SSE API as the static frontend.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Queue and result-store health |
| `POST` | `/simulate` | Generate and queue transactions |
| `GET` | `/simulate/stream` | Stream prediction results with SSE |
| `GET` | `/dashboard/stats` | Session statistics and breakdowns |
| `GET` | `/dashboard/feed` | Recent processed transactions |
| `GET` | `/dashboard/alerts` | Recent blocked transactions and reasoning |
| `POST` | `/dashboard/reset` | Clear in-memory session results |

Example simulation request:

```powershell
curl.exe -X POST http://127.0.0.1:8000/simulate `
  -H "Content-Type: application/json" `
  -d '{"mode":"stolen_card","num_transactions":5}'
```

Supported modes are `normal`, `stolen_card`, `geo_attack`, and `velocity_burst`. Use an attack mode to produce blocked transactions and LLM explanations.

## Train and Register a Model

The training pipeline uses the sampled CSV files by default:

```powershell
python -m src.pipelines.ml_pipeline --limit 30000
```

The `--limit` option limits training rows. Omit it to use the complete training sample. The pipeline evaluates candidates, selects the highest-recall run, logs the preprocessor into the same MLflow run, and manages the model registry lifecycle.

You can also call the pipeline from Python:

```python
from src.pipelines.ml_pipeline import MLPipeline

MLPipeline(limit=30000).run_pipeline()
```

## Testing

Run the complete test suite:

```powershell
python -m pytest tests -q
```

The same command runs in GitHub Actions on Python 3.11. Tests cover ingestion, transformation, feature engineering, preparation, model components, prediction preprocessing, reasoning helpers, simulation, streaming orchestration, routes, and utilities.

For a focused local check:

```powershell
python -m pytest -q tests/test_predictor.py tests/test_reasoning.py tests/test_streaming_pipeline.py
```

## Model and Inference Details

The fitted preprocessor one-hot encodes `buyer_gender` and `category`, then standardizes numeric features. The production predictor uses the following model features:

```text
category
buyer_gender
transaction_hour
buyer_age
distance_km
transaction_amount_log
is_night_transaction
```

A fraud probability of `0.50` or higher produces a `BLOCKED` decision. LLM reasoning is requested only for blocked transactions. If the provider returns no visible content, the API returns an automated risk summary so the alert remains informative.

## CI

The workflow in `.github/workflows/ci.yml` runs on pushes and pull requests targeting `main`:

1. Installs Python 3.11.
2. Installs `requirements.txt`.
3. Runs `python -m pytest tests -q`.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
