"""
Streaming-Inspired Pipeline DAG
Simulates real-time data processing by running every minute
Processes only new data since last run (incremental processing)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from pathlib import Path
import random

# Define paths
BASE_DIR = Path('C:/Users/vPro/airflow-docker')  # Adjust to your Airflow home directory
STREAMING_DIR = BASE_DIR / 'data' / 'streaming'
STATE_DIR = STREAMING_DIR / 'state'
INCOMING_DIR = STREAMING_DIR / 'incoming'
PROCESSED_DIR = STREAMING_DIR / 'processed'

# Ensure directories exist
for dir_path in [STATE_DIR, INCOMING_DIR, PROCESSED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# State file to track last processed timestamp
STATE_FILE = STATE_DIR / 'last_processed_timestamp.json'


def generate_streaming_data(**context):
    """
    Simulates a streaming data source that continuously produces new records
    In production, this could be:
    - IoT sensor data
    - Application logs
    - User clickstream events
    - Real-time transactions
    - Social media feeds
    """
    print("Generating new streaming data...")
    
    # Get current execution time
    current_time = datetime.now()
    
    # Generate random number of events (simulating variable traffic)
    num_events = random.randint(5, 20)
    
    # Simulate IoT sensor data
    events = []
    for i in range(num_events):
        event = {
            'event_id': f'EVT_{current_time.timestamp()}_{i}',
            'sensor_id': f'SENSOR_{random.randint(1, 10):03d}',
            'temperature': round(random.uniform(18.0, 28.0), 2),
            'humidity': round(random.uniform(30.0, 70.0), 2),
            'pressure': round(random.uniform(980.0, 1020.0), 2),
            'status': random.choice(['normal', 'warning', 'critical']),
            'timestamp': (current_time - timedelta(seconds=random.randint(0, 60))).isoformat(),
            'location': random.choice(['Building_A', 'Building_B', 'Building_C', 'Building_D'])
        }
        events.append(event)
    
    # Save to incoming directory
    filename = f'events_{current_time.strftime("%Y%m%d_%H%M%S")}.json'
    filepath = INCOMING_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(events, f, indent=2)
    
    print(f"Generated {num_events} events and saved to {filepath}")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='new_events_file', value=str(filepath))
    context['task_instance'].xcom_push(key='event_count', value=num_events)
    
    return str(filepath)


def get_last_processed_timestamp():
    """Helper function to get the last processed timestamp"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            return datetime.fromisoformat(state['last_processed_timestamp'])
    return None


def update_last_processed_timestamp(timestamp):
    """Helper function to update the last processed timestamp"""
    with open(STATE_FILE, 'w') as f:
        json.dump({
            'last_processed_timestamp': timestamp.isoformat(),
            'updated_at': datetime.now().isoformat()
        }, f, indent=2)


def ingest_new_data(**context):
    """
    Ingest task: Reads only NEW data since last run
    This is the key difference from batch processing - incremental ingestion
    """
    print("Ingesting new streaming data...")
    
    # Get the last processed timestamp
    last_processed = get_last_processed_timestamp()
    print(f"Last processed timestamp: {last_processed}")
    
    # Read all files in incoming directory
    all_events = []
    files_processed = []
    
    for file_path in INCOMING_DIR.glob('events_*.json'):
        with open(file_path, 'r') as f:
            events = json.load(f)
            
            # Filter only new events
            for event in events:
                event_time = datetime.fromisoformat(event['timestamp'])
                
                # Only process events newer than last processed timestamp
                if last_processed is None or event_time > last_processed:
                    all_events.append(event)
            
            files_processed.append(str(file_path))
    
    if not all_events:
        print("No new events to process")
        context['task_instance'].xcom_push(key='has_new_data', value=False)
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(all_events)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    print(f"Ingested {len(df)} new events from {len(files_processed)} files")
    
    # Save ingested data
    execution_time = context['execution_date'].strftime('%Y%m%d_%H%M%S')
    ingested_file = STREAMING_DIR / f'ingested_{execution_time}.csv'
    df.to_csv(ingested_file, index=False)
    
    # Push to XCom
    context['task_instance'].xcom_push(key='ingested_file', value=str(ingested_file))
    context['task_instance'].xcom_push(key='event_count', value=len(df))
    context['task_instance'].xcom_push(key='has_new_data', value=True)
    
    return str(ingested_file)


def transform_streaming_data(**context):
    """
    Transform task: Process streaming data in real-time
    - Validate data quality
    - Enrich with additional information
    - Calculate running aggregations
    - Detect anomalies
    """
    print("Transforming streaming data...")
    
    # Check if there's new data
    has_new_data = context['task_instance'].xcom_pull(task_ids='ingest', key='has_new_data')
    
    if not has_new_data:
        print("No new data to transform")
        return None
    
    # Get ingested file
    ingested_file = context['task_instance'].xcom_pull(task_ids='ingest', key='ingested_file')
    df = pd.read_csv(ingested_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"Transforming {len(df)} events")
    
    # Data Validation
    # 1. Check for valid sensor readings
    df['is_valid'] = (
        (df['temperature'] >= -50) & (df['temperature'] <= 50) &
        (df['humidity'] >= 0) & (df['humidity'] <= 100) &
        (df['pressure'] >= 900) & (df['pressure'] <= 1100)
    )
    
    # 2. Flag anomalies
    df['temp_anomaly'] = (df['temperature'] < 15) | (df['temperature'] > 30)
    df['humidity_anomaly'] = (df['humidity'] < 20) | (df['humidity'] > 80)
    
    # Data Enrichment
    # 1. Add time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # 2. Calculate comfort index
    df['comfort_index'] = (
        (df['temperature'] >= 20) & (df['temperature'] <= 25) &
        (df['humidity'] >= 40) & (df['humidity'] <= 60)
    ).astype(int)
    
    # 3. Add processing metadata
    df['processed_at'] = datetime.now()
    df['processing_latency_ms'] = (
        pd.to_datetime(df['processed_at']) - df['timestamp']
    ).dt.total_seconds() * 1000
    
    # Real-time Aggregations
    # Calculate rolling averages per sensor (last 10 readings)
    sensor_stats = df.groupby('sensor_id').agg({
        'temperature': ['mean', 'std', 'min', 'max'],
        'humidity': ['mean', 'std'],
        'event_id': 'count'
    }).round(2)
    
    # Alert Detection
    critical_events = df[df['status'] == 'critical']
    anomaly_events = df[df['temp_anomaly'] | df['humidity_anomaly']]
    
    # Save transformed data
    execution_time = context['execution_date'].strftime('%Y%m%d_%H%M%S')
    transformed_file = PROCESSED_DIR / f'processed_{execution_time}.csv'
    df.to_csv(transformed_file, index=False)
    
    # Save aggregations
    stats_file = PROCESSED_DIR / f'sensor_stats_{execution_time}.json'
    stats = {
        'total_events': len(df),
        'valid_events': df['is_valid'].sum(),
        'critical_events': len(critical_events),
        'anomalies_detected': len(anomaly_events),
        'avg_processing_latency_ms': df['processing_latency_ms'].mean(),
        'sensors_reporting': df['sensor_id'].nunique(),
        'timestamp_range': {
            'start': df['timestamp'].min().isoformat(),
            'end': df['timestamp'].max().isoformat()
        }
    }
    
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Transformed data saved to {transformed_file}")
    print(f"Statistics: {stats}")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='transformed_file', value=str(transformed_file))
    context['task_instance'].xcom_push(key='stats', value=stats)
    context['task_instance'].xcom_push(key='latest_timestamp', 
                                        value=df['timestamp'].max().isoformat())
    
    return str(transformed_file)


def load_streaming_data(**context):
    """
    Load task: Store processed streaming data
    In production, this could be:
    - Time-series database (InfluxDB, TimescaleDB)
    - Real-time analytics platform (Druid, Pinot)
    - Message queue for downstream consumers
    - Real-time dashboard updates
    """
    print("Loading streaming data...")
    
    # Check if there's new data
    has_new_data = context['task_instance'].xcom_pull(task_ids='ingest', key='has_new_data')
    
    if not has_new_data:
        print("No new data to load")
        return None
    
    # Get transformed file and stats
    transformed_file = context['task_instance'].xcom_pull(task_ids='transform_stream', 
                                                           key='transformed_file')
    stats = context['task_instance'].xcom_pull(task_ids='transform_stream', key='stats')
    latest_timestamp = context['task_instance'].xcom_pull(task_ids='transform_stream', 
                                                           key='latest_timestamp')
    
    # Read transformed data
    df = pd.read_csv(transformed_file)
    
    # Simulate loading to time-series database
    # In production:
    # from influxdb_client import InfluxDBClient
    # client.write_api().write(bucket="sensors", record=df)
    
    # Append to cumulative dataset
    cumulative_file = PROCESSED_DIR / 'streaming_data_cumulative.csv'
    if cumulative_file.exists():
        existing_df = pd.read_csv(cumulative_file)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        # Keep only last 10000 records to prevent unlimited growth
        combined_df = combined_df.tail(10000)
    else:
        combined_df = df
    
    combined_df.to_csv(cumulative_file, index=False)
    
    # Update state file with latest timestamp
    update_last_processed_timestamp(datetime.fromisoformat(latest_timestamp))
    
    print(f"Loaded {len(df)} events to destination")
    print(f"Updated state file with timestamp: {latest_timestamp}")
    print(f"Statistics: {stats}")
    
    # Generate alerts if needed
    if stats['critical_events'] > 0:
        print(f"⚠️ ALERT: {stats['critical_events']} critical events detected!")
    
    if stats['anomalies_detected'] > 0:
        print(f"⚠️ WARNING: {stats['anomalies_detected']} anomalies detected!")
    
    return {
        'status': 'success',
        'records_loaded': len(df),
        'total_records': len(combined_df),
        'critical_events': stats['critical_events']
    }


def cleanup_old_files(**context):
    """
    Cleanup task: Remove old incoming files to prevent storage issues
    """
    print("Cleaning up old files...")
    
    # Get files older than 1 hour
    cutoff_time = datetime.now() - timedelta(hours=1)
    files_deleted = 0
    
    for file_path in INCOMING_DIR.glob('events_*.json'):
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_time < cutoff_time:
            file_path.unlink()
            files_deleted += 1
    
    print(f"Deleted {files_deleted} old incoming files")
    
    return files_deleted


# Define default arguments
default_args = {
    'owner': 'streaming_team',
    'depends_on_past': False,
    'email': ['streaming-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
    'execution_timeout': timedelta(minutes=2),
}

# Define the DAG
with DAG(
    dag_id='streaming_sensor_pipeline',
    default_args=default_args,
    description='Streaming-inspired pipeline for IoT sensor data - runs every minute',
    schedule_interval='* * * * *',  # Every minute (cron format)
    start_date=days_ago(1),
    catchup=False,
    tags=['streaming', 'iot', 'realtime', 'sensors'],
    max_active_runs=1,
) as dag:
    
    # Define tasks
    generate_task = PythonOperator(
        task_id='generate_data',
        python_callable=generate_streaming_data,
        provide_context=True,
    )
    
    ingest_task = PythonOperator(
        task_id='ingest',
        python_callable=ingest_new_data,
        provide_context=True,
    )
    
    transform_task = PythonOperator(
        task_id='transform_stream',
        python_callable=transform_streaming_data,
        provide_context=True,
    )
    
    load_task = PythonOperator(
        task_id='load',
        python_callable=load_streaming_data,
        provide_context=True,
    )
    
    cleanup_task = PythonOperator(
        task_id='cleanup',
        python_callable=cleanup_old_files,
        provide_context=True,
    )
    
    # Define task dependencies
    generate_task >> ingest_task >> transform_task >> load_task >> cleanup_task