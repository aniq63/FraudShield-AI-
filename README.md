# FraudShield AI – Real-Time Fraud Detection System

<div align="center">

**Production-Grade Fraud Detection with Machine Learning + LLM Reasoning**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange?style=for-the-badge)](https://xgboost.readthedocs.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL-green?style=for-the-badge&logo=mongodb)](https://www.mongodb.com/)
[![AWS S3](https://img.shields.io/badge/AWS%20S3-Cloud%20Storage-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/s3/)

</div>

---

## Live Demo

**[Try FraudShield AI Now](https://fraudshields-ai.vercel.app/)** – https://fraudshields-ai.vercel.app/

Explore the real-time dashboard, run transaction simulations, and see fraud detection in action!

---

## Overview

**FraudShield AI** is a production-ready fraud detection system that monitors financial transactions in real-time and predicts whether a transaction is fraudulent before approval. The system combines:

- **Machine Learning Models** (XGBoost, Random Forest, Logistic Regression) for fast, accurate predictions
- **LLM-Based Reasoning** (Groq/LangChain) for explainable decision-making
- **Real-Time Streaming Pipeline** for sub-second fraud detection
- **Professional Dashboard** for transaction monitoring and analytics
- **AWS S3 Integration** for model persistence and scalability
- **MongoDB** for flexible transaction data storage

---

## Key Features

### Real-Time Processing
- **Sub-second latency** fraud detection for production transactions
- **Streaming pipeline** with multi-threaded consumer-producer architecture
- **Live dashboards** with real-time transaction updates via SSE (Server-Sent Events)

### Intelligent Detection
- **Multi-model ensemble** (XGBoost, Random Forest, Logistic Regression)
- **Advanced feature engineering** including:
  - Geographical distance calculation
  - Night transaction flagging
  - Category-based patterns
  - Amount anomaly detection
- **LLM-powered reasoning** for explainable fraud decisions
- **Class imbalance handling** with weighted sampling

### Comprehensive Monitoring
- **Live dashboard** with transaction statistics and fraud metrics
- **Historical analytics** with fraud trends and patterns
- **MLflow integration** for experiment tracking and model versioning
- **In-memory result store** with SSE real-time streaming

### Production-Ready
- **Containerizable architecture** with FastAPI
- **CORS-enabled** for frontend integration
- **Error handling and logging** throughout the pipeline
- **Scalable database design** with MongoDB
- **Cloud storage** with AWS S3 for models

### Transaction Simulation
Multiple transaction generation modes for realistic testing:
- **Normal transactions**: Everyday legitimate purchases
- **Stolen card attacks**: High-value unauthorized transactions
- **Geo attacks**: Impossible-distance fraud patterns
- **Phishing attacks**: Category-based fraud patterns

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FraudShield AI Pipeline                      │
└─────────────────────────────────────────────────────────────────┘

INPUT LAYER
    ↓
    ├─ Transaction Generator (Simulator)
    ├─ Real Transaction Stream
    └─ API Endpoints

DATA PROCESSING
    ↓
    ├─ Data Ingestion (MongoDB)
    ├─ ETL Pipeline (Extract, Transform, Load)
    ├─ Feature Engineering
    └─ Data Preparation & Normalization

ML INFERENCE
    ↓
    ├─ Model Loading (S3 → Memory)
    ├─ Preprocessing (StandardScaler)
    ├─ Multi-Model Prediction
    │   ├─ XGBoost (Primary)
    │   ├─ Random Forest
    │   ├─ Logistic Regression
    │   └─ Ensemble voting
    └─ LLM Reasoning (Groq)

OUTPUT LAYER
    ↓
    ├─ FastAPI REST Endpoints
    ├─ Real-Time Dashboard
    ├─ Live Analytics
    └─ Result Store (In-Memory)
```

---

## Dataset

**Dataset**: [Fraud Detection - Kaggle](https://www.kaggle.com/datasets/kartik2112/fraud-detection)

### Dataset Characteristics:
- **~1.3M transactions** with fraud labels
- **Features**:
  - `transaction_amount`: Transaction value (USD)
  - `transaction_hour`: Hour of day (0-23)
  - `category`: Transaction category (grocery_pos, shopping_net, etc.)
  - `buyer_age`: Customer age
  - `location_coordinates`: Geographical location
  - `transaction_is_fraud`: Target label (0=Legitimate, 1=Fraud)

### Key Statistics:
- **Class Distribution**: ~0.2% fraudulent (highly imbalanced)
- **Fraud Distribution**:
  - Night transactions: 80.5% fraud rate
  - Top categories: grocery_pos (34%), shopping_net (22%), gas_transport (17%)
  - Amount range: $50-$1,250
  - Buyer age: Fraud avg 59.8 years vs Normal 45.5 years

---

## Technology Stack

### Backend & ML
| Technology | Purpose |
|-----------|---------|
| **Python 3.8+** | Core language |
| **FastAPI** | REST API framework |
| **XGBoost** | Primary ML model |
| **scikit-learn** | ML utilities & preprocessing |
| **Pandas** | Data manipulation |
| **NumPy** | Numerical computing |
| **joblib** | Model serialization |

### Data & Storage
| Technology | Purpose |
|-----------|---------|
| **MongoDB** | Transaction database |
| **AWS S3** | Model & artifact storage |
| **MLflow** | Experiment tracking |

### LLM & Reasoning
| Technology | Purpose |
|-----------|---------|
| **LangChain** | LLM orchestration |
| **Groq** | Fast LLM inference |

### Frontend & Monitoring
| Technology | Purpose |
|-----------|---------|
| **HTML5/CSS3/JS** | Dashboard UI |
| **FastAPI SSE** | Real-time updates |

---

## Installation

> **Want to try it first?** Check out the [live demo](https://fraudshields-ai.vercel.app/) to see FraudShield AI in action before installing locally!

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud)
- AWS S3 bucket (for model storage)
- Groq API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/FraudShield-AI.git
   cd FraudShield-AI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # - MONGO_URI
   # - AWS_ACCESS_KEY_ID
   # - AWS_SECRET_ACCESS_KEY
   # - AWS_S3_BUCKET
   # - GROQ_API_KEY
   ```

5. **Verify MongoDB connection**
   ```bash
   python mongo_test.py
   ```

6. **Run the API server**
   ```bash
   python main.py
   ```
   Server runs at `http://localhost:8000`

7. **Access the dashboard**
   - Open `frontend/dashboard.html` in your browser
   - Or navigate to `http://localhost:8000/docs` for API documentation

---

## Usage

### 1. **Run Demo (Console Output)**
```bash
python demo.py                              # 10 stolen_card transactions
python demo.py --mode geo_attack --n 5     # 5 geo-attack transactions
python demo.py --mode normal --n 20        # 20 legitimate transactions
```

### 2. **Train ML Pipeline**
```python
from src.pipelines.ml_pipeline import MLPipeline

pipeline = MLPipeline(
    mongo_collection_name="transactions",
    limit=10000  # Train on first 10k
)
pipeline.run_pipeline()
```

### 3. **Make Predictions via API**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_amount": 450.00,
    "transaction_hour": 2,
    "category": "grocery_pos",
    "buyer_age": 65,
    "location_coordinates": [40.7128, -74.0060]
  }'
```

### 4. **Real-Time Streaming**
```bash
curl -N "http://localhost:8000/stream"
```

### 5. **Get Transaction History**
```bash
curl "http://localhost:8000/results"
```

---

## Dashboard Previews

### Dashboard Overview
![Dashboard](images/C1.PNG)

### Analytics & Metrics
![Analytics](images/c2.PNG)

### Fraud Detection Interface
![Detection](images/c3.PNG)

---

## Model Performance

### Training Metrics
- **Best Model**: XGBoost with balanced class weights
- **F1 Score**: ~0.85-0.90 (optimized for fraud recall)
- **Precision**: ~0.82-0.87
- **Recall**: ~0.88-0.92 (critical for fraud detection)
- **Training Time**: ~2-5 minutes (10k transactions)

### Inference Performance
- **Latency**: <100ms per transaction
- **Throughput**: 10,000+ transactions/second
- **Model Size**: ~5-10 MB (fits in memory)

---

## Project Structure

```
FraudShield-AI/
├── src/
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints
│   ├── components/
│   │   ├── data_ingestion.py      # MongoDB data fetching
│   │   ├── data_preparation.py    # Data cleaning
│   │   ├── data_feature_engineering.py
│   │   ├── model_trainer.py       # Model training
│   │   └── model_evaluation.py    # Performance metrics
│   ├── cloud/
│   │   └── s3_manager.py          # AWS S3 integration
│   ├── db/
│   │   └── mongo_connection.py    # MongoDB client
│   ├── ETL/
│   │   ├── extraction.py
│   │   ├── transformation.py
│   │   └── load.py
│   ├── inference/
│   │   ├── predictor.py           # ML predictions
│   │   └── reasoning.py           # LLM explanations
│   ├── pipelines/
│   │   ├── etl_pipeline.py
│   │   ├── ml_pipeline.py         # End-to-end ML pipeline
│   │   └── streaming_pipeline.py  # Real-time processing
│   ├── simulator/
│   │   └── transaction_generator.py
│   └── utils/
│       ├── logging.py
│       └── exception.py
├── frontend/
│   ├── dashboard.html             # Main dashboard UI
│   ├── index.html
│   └── simulator.html
├── notebooks/
│   └── Fraud Detection system.ipynb
├── main.py                        # FastAPI server entry point
├── demo.py                        # Console demo script
├── requirements.txt
└── README.md
```

---

## Pipeline Overview

### ML Pipeline Stages:
1. **Data Extraction** → Fetch from MongoDB
2. **Data Transformation** → Clean & normalize
3. **Feature Engineering** → Create derived features
4. **Data Preparation** → Split & scale
5. **Model Training** → Train multiple models
6. **Model Evaluation** → Compute metrics
7. **Model Upload** → Save to S3
8. **MLflow Tracking** → Log experiments

### Streaming Pipeline:
1. **Transaction Generation** → Create test transactions
2. **Prediction** → Load model, preprocess, predict
3. **LLM Reasoning** → Explain decision
4. **Result Storage** → In-memory + Database
5. **Real-Time Broadcast** → SSE to dashboard

---

## Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t fraudshield-ai .
docker run -p 8000:8000 --env-file .env fraudshield-ai
```

---

## 📈 Monitoring & Logging

- **Structured logging** in `src/utils/logging.py`
- **MLflow dashboard** at `http://localhost:5000` (after `mlflow ui`)
- **FastAPI Swagger UI** at `http://localhost:8000/docs`
- **Results stored** in memory (deque with max 5000 entries)

---

## Environment Variables

```
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/fraudshield
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
GROQ_API_KEY=your-groq-key
HOST=0.0.0.0
PORT=8000
DEBUG=false
ALLOWED_ORIGINS=*
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Support & Contact

For questions, issues, or suggestions:
- **GitHub Issues**: Open an issue on the repository
- **Email**: your-email@example.com

---

## Learning Resources

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [Kaggle Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection)

---

<div align="center">

**Made with ❤️ for secure financial transactions**

⭐ If this project helped you, please consider giving it a star!

</div>
