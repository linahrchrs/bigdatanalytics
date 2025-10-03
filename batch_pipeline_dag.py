from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd

# ---------- Mock ETL functions ----------
def extract():
    # Simulate data extraction (could be from API, DB, etc.)
    data = {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
    }
    df = pd.DataFrame(data)
    df.to_csv("/tmp/raw_data.csv", index=False)

def transform():
    df = pd.read_csv("/tmp/raw_data.csv")
    # Example transformation: filter + uppercase names
    df = df[df["age"] > 26]
    df["name"] = df["name"].str.upper()
    df.to_csv("/tmp/transformed_data.csv", index=False)

def load():
    df = pd.read_csv("/tmp/transformed_data.csv")
    # Load to destination (here: just saving final file)
    df.to_csv("/tmp/final_data.csv", index=False)

# ---------- DAG definition ----------
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "batch_pipeline",
    default_args=default_args,
    description="Batch ETL pipeline with Airflow",
    schedule_interval=timedelta(hours=2),  # runs every 2 hours
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    extract_task >> transform_task >> load_task
