import sqlite3
import numpy as np
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from joblib import dump

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'db.sqlite3'
MODEL_PATH = BASE_DIR / 'pump_decision_model.joblib'

TABLE_NAME = 'sensor_data_sensordata'
FEATURE_COLUMNS = ['temperature', 'humidity', 'soil_moisture']


def load_data_from_sqlite(db_path: Path) -> np.ndarray:
    if not db_path.exists():
        raise FileNotFoundError(f'Database not found at: {db_path}')

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        # Ensure table exists
        cur.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
        """, (TABLE_NAME,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f'Table {TABLE_NAME} not found in {db_path}')

        cols = ','.join(FEATURE_COLUMNS + ['timestamp'])
        cur.execute(f"SELECT {cols} FROM {TABLE_NAME} ORDER BY timestamp ASC")
        rows = cur.fetchall()
        if not rows:
            raise RuntimeError('No sensor data found to train the model.')

        X = []
        for r in rows:
            temperature, humidity, soil_moisture, _ts = r
            X.append([temperature, humidity, soil_moisture])

        X = np.array(X, dtype=float)

        return X
    finally:
        conn.close()


class KMeansPumpWrapper:
    def __init__(self, imputer: SimpleImputer, kmeans: KMeans, on_label: int):
        self.imputer = imputer
        self.kmeans = kmeans
        self.on_label = on_label  # cluster label that corresponds to ON (1)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        X_imp = self.imputer.transform(X)
        labels = self.kmeans.predict(X_imp)
        # Map labels to 0/1 using on_label
        return (labels == self.on_label).astype(int)


def train_and_save_model(X: np.ndarray, model_path: Path) -> None:
    if len(X) < 10:
        # Not enough rows; still try to fit but warn
        print(f'Warning: Only {len(X)} rows available. Model quality may be poor.')

    # Handle missing values just in case
    imputer = SimpleImputer(strategy='median')
    X_imp = imputer.fit_transform(X)

    # Fit KMeans with 2 clusters
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    kmeans.fit(X_imp)

    # Decide which cluster is ON: choose cluster with LOWER soil_moisture mean
    labels = kmeans.labels_
    soil_idx = 2
    cluster0_mean_soil = X_imp[labels == 0][:, soil_idx].mean() if np.any(labels == 0) else np.inf
    cluster1_mean_soil = X_imp[labels == 1][:, soil_idx].mean() if np.any(labels == 1) else np.inf
    on_label = 0 if cluster0_mean_soil < cluster1_mean_soil else 1

    wrapper = KMeansPumpWrapper(imputer=imputer, kmeans=kmeans, on_label=on_label)

    # Save as joblib at the exact path used by the app
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    dump(wrapper, str(model_path))
    print(f"Model (KMeans wrapper) saved to: {model_path}\nON cluster label: {on_label} (lower soil moisture)")


if __name__ == '__main__':
    print(f'Loading data from {DB_PATH} ...')
    X = load_data_from_sqlite(DB_PATH)
    print(f'Dataset size: {len(X)} rows, features: {X.shape[1]}')

    print('Training KMeans (unsupervised) model ...')
    train_and_save_model(X, MODEL_PATH)
