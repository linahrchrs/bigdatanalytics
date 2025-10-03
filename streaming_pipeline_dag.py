from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import os

# Simulated streaming data file
DATA_FILE = "/tmp/streaming_data.csv"
PROCESSED_FILE = "/tmp/processed_data.csv"

def generate_new_data():
    # Append new rows as if they are "arriving"
    new_data = pd.DataFrame({
        "id": [datetime.now().strftime("%H%M%S")],
        "value": [datetime.now().second]  # just a random number
    })
    if not os.path.exists(DATA_FILE):
        new_data.to_csv(DATA_FILE, index=False)
    else:
        new_data.to_csv(DATA_FILE, mode="a", header=False, index=False)

def extract_new_data():
    df = pd.read_csv(DATA_FILE)
    # Track which rows were already processed
    if os.path.exists(PROCESSED_FILE):
        processed = pd.read_csv(PROCESSED_FILE)
        df = df[~df["id"].isin(processed["id"])]
    df.to_csv("/tmp/new_data.csv", index=False)

def transform_new_data():
    df = pd.read_csv("/tmp/new_data.csv")
    if not df.empty:
        df["value_squared"] = df["value"] ** 2
        df.to_csv("/tmp/new_data_transformed.csv", index=False)

def load_new_data():
    if os.path.exists("/tmp/new_data_transformed.csv"):
        df = pd.read_csv("/tmp/new_data_transformed.csv")
        if not df.empty:
            if not os.path.exists(PROCESSED_FILE):
                df.to_csv(PROCESSED_FILE, index=False)
            else:
                df.to_csv(PROCESSED_FILE, mode="a", header=False, index=False)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
}

with DAG(
    "streaming_pipeline",
    default_args=default_args,
    description="Streaming-inspired micro-batch pipeline",
    schedule_interval="* * * * *",  # every minute
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    generate_task = PythonOperator(task_id="generate", python_callable=generate_new_data)
    extract_task = PythonOperator(task_id="extract", python_callable=extract_new_data)
    transform_task = PythonOperator(task_id="transform", python_callable=transform_new_data)
    load_task = PythonOperator(task_id="load", python_callable=load_new_data)

    generate_task >> extract_task >> transform_task >> load_task
