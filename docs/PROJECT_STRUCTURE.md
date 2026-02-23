# EnerSight Project Structure

This document explains the folder structure and purpose of each component.

## 📁 Root Directory

```
EnerSight/
├── backend/              # FastAPI backend application
├── ml/                   # Machine learning models and training
├── frontend/             # React dashboard
├── data/                 # Dataset storage
├── scripts/              # Utility scripts
├── configs/              # Configuration files
├── docs/                 # Documentation
├── tests/                # Unit and integration tests
├── logs/                 # Application logs
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── requirements.txt     # Python dependencies
└── README.md            # Project overview
```

## 🔧 Backend (`/backend`)

FastAPI-based REST API server for the platform.

```
backend/
├── __init__.py
├── main.py                    # FastAPI app entry point
├── api/                       # API routes and endpoints
│   ├── __init__.py
│   ├── routes/               # Route handlers
│   │   ├── energy.py         # Energy data endpoints
│   │   ├── predictions.py    # ML prediction endpoints
│   │   └── anomalies.py      # Anomaly detection endpoints
│   └── models/               # Pydantic schemas
│       ├── __init__.py
│       └── energy.py         # Data validation models
├── database/                  # Database connections
│   ├── __init__.py
│   └── influxdb_client.py    # InfluxDB time-series DB
└── services/                  # Business logic
    └── mqtt_service.py        # MQTT client for IoT devices
```

**Purpose**: 
- Handle HTTP requests from dashboard
- Store/retrieve time-series energy data
- Serve ML predictions
- Process MQTT sensor data

## 🤖 Machine Learning (`/ml`)

ML models for prediction and anomaly detection.

```
ml/
├── __init__.py
├── models/                        # Model implementations
│   ├── regression_model.py        # Scikit-learn regression
│   ├── lstm_model.py              # TensorFlow LSTM for forecasting
│   └── anomaly_detector.py        # Isolation Forest for anomalies
├── preprocessing/                 # Data preprocessing
│   ├── data_preprocessing.py      # Cleaning, normalization
│   └── feature_engineering.py     # Feature creation
├── training/                      # Training scripts
│   └── train_models.py            # Main training pipeline
└── models/trained/                # Saved trained models
    ├── regression_random_forest.joblib
    ├── lstm_energy_forecast.keras
    └── anomaly_detector.joblib
```

**Purpose**:
- Train ML models on historical data
- Make real-time predictions
- Detect unusual consumption patterns
- Feature engineering for better accuracy

## 🎨 Frontend (`/frontend`)

React-based dashboard for visualization.

```
frontend/
├── package.json              # Node.js dependencies
├── vite.config.js           # Vite build configuration
├── index.html               # HTML entry point
└── src/
    ├── main.jsx             # React entry point
    ├── App.jsx              # Main app component
    ├── index.css            # Global styles
    ├── components/          # Reusable components
    │   └── Layout.jsx       # App layout with sidebar
    ├── pages/               # Page components
    │   ├── Dashboard.jsx    # Main dashboard
    │   ├── RealTime.jsx     # Live monitoring
    │   ├── Analytics.jsx    # Historical analysis
    │   ├── Predictions.jsx  # Forecasts
    │   └── Anomalies.jsx    # Anomaly alerts
    └── services/            # API services
        └── api.js           # Axios API client
```

**Purpose**:
- Display real-time energy consumption
- Visualize trends with charts
- Show predictions and anomalies
- User-friendly interface

## 💾 Data (`/data`)

Dataset storage organized by processing stage.

```
data/
├── raw/                          # Original unprocessed data
│   └── Energy_consumption.csv    # Your dataset
├── processed/                    # Cleaned and transformed data
│   └── energy_data_cleaned.csv
└── sample/                       # Sample data for testing
```

**Purpose**:
- Store original dataset
- Keep processed versions
- Maintain data pipeline

## 🛠️ Scripts (`/scripts`)

Utility scripts for setup and operations.

```
scripts/
├── mqtt_simulator.py             # Simulate IoT sensors
└── load_data_to_influxdb.py     # Import CSV to InfluxDB
```

**Purpose**:
- Simulate real-time sensor data
- Load historical data into database
- Automation and testing

## ⚙️ Configuration (`/configs`)

Configuration files for various services.

```
configs/
├── grafana/                 # Grafana dashboards
├── nodered/                 # Node-RED flows
└── influxdb/                # InfluxDB configuration
```

**Purpose**:
- Pre-configured Grafana dashboards
- Node-RED workflow automation
- Service configurations

## 📝 Documentation (`/docs`)

Project documentation and guides.

```
docs/
├── architecture.md          # System architecture
├── api_documentation.md     # API endpoints reference
├── setup_guide.md          # Installation instructions
└── ml_models.md            # ML model documentation
```

## ✅ Tests (`/tests`)

Unit and integration tests.

```
tests/
├── __init__.py
├── test_api.py             # API endpoint tests
├── test_models.py          # ML model tests
└── test_data.py            # Data processing tests
```

## 📊 Logs (`/logs`)

Application logs for debugging.

```
logs/
├── app.log                 # General application logs
├── ml_training.log         # Model training logs
└── mqtt.log               # IoT communication logs
```

## 🔑 Key Files

- **`.env.example`**: Template for environment variables (database credentials, API keys)
- **`requirements.txt`**: Python package dependencies
- **`README.md`**: Project overview and quick start guide
- **`.gitignore`**: Files to exclude from version control

## 🚀 Data Flow

1. **Data Ingestion**: IoT sensors → MQTT → Backend → InfluxDB
2. **Processing**: Raw data → Preprocessing → Feature Engineering
3. **ML Pipeline**: Training data → ML Models → Predictions
4. **Visualization**: InfluxDB/API → Frontend Dashboard → User
5. **Monitoring**: Real-time data → Anomaly Detection → Alerts

## 🔄 Development Workflow

1. Place dataset in `data/raw/`
2. Train ML models: `python ml/training/train_models.py`
3. Start backend: `uvicorn backend.main:app --reload`
4. Start frontend: `cd frontend && npm run dev`
5. Simulate sensors: `python scripts/mqtt_simulator.py`
6. View dashboard: `http://localhost:3000`

---

This structure follows best practices for:
- ✅ Separation of concerns
- ✅ Scalability
- ✅ Maintainability
- ✅ Clear organization
- ✅ Easy collaboration
