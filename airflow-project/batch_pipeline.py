"""
Batch Processing Pipeline DAG
Processes sales data every 2 hours: extracts, transforms, and loads to database/file
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from pathlib import Path

# Define paths
BASE_DIR = Path('C:/Users/vPro/airflow-docker')  # Adjust to your Airflow home directory
SOURCE_DIR = BASE_DIR / 'data' / 'source'
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'

# Ensure directories exist
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def extract_data(**context):
    """
    Extract task: Reads data from source
    In production, this could be:
    - API calls
    - Database queries
    - S3 bucket reads
    - CSV/JSON file ingestion
    """
    print("Starting data extraction...")
    
    # Simulate data extraction (in real scenario, this would be from API/DB)
    # Generate sample sales data
    data = {
        'transaction_id': range(1001, 1101),
        'customer_id': [f'CUST{i%50:03d}' for i in range(100)],
        'product': ['Product_A', 'Product_B', 'Product_C', 'Product_D'] * 25,
        'quantity': [i % 10 + 1 for i in range(100)],
        'price': [19.99, 29.99, 39.99, 49.99] * 25,
        'timestamp': [datetime.now() - timedelta(hours=i) for i in range(100)],
        'region': ['North', 'South', 'East', 'West'] * 25
    }
    
    df = pd.DataFrame(data)
    
    # Save raw data
    execution_date = context['execution_date'].strftime('%Y%m%d_%H%M%S')
    raw_file = SOURCE_DIR / f'raw_data_{execution_date}.csv'
    df.to_csv(raw_file, index=False)
    
    print(f"Extracted {len(df)} records to {raw_file}")
    
    # Push file path to XCom for next task
    context['task_instance'].xcom_push(key='raw_file_path', value=str(raw_file))
    context['task_instance'].xcom_push(key='record_count', value=len(df))
    
    return str(raw_file)


def transform_data(**context):
    """
    Transform task: Cleans and processes data
    - Handle missing values
    - Data validation
    - Calculate derived metrics
    - Filter outliers
    """
    print("Starting data transformation...")
    
    # Get file path from previous task
    raw_file = context['task_instance'].xcom_pull(task_ids='extract', key='raw_file_path')
    
    # Read data
    df = pd.read_csv(raw_file)
    print(f"Loaded {len(df)} records for transformation")
    
    # Data Cleaning
    # 1. Remove duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=['transaction_id'])
    print(f"Removed {initial_count - len(df)} duplicates")
    
    # 2. Handle missing values
    df = df.dropna()
    
    # 3. Data validation - remove invalid quantities
    df = df[df['quantity'] > 0]
    df = df[df['price'] > 0]
    
    # Data Transformation
    # 1. Calculate total amount
    df['total_amount'] = df['quantity'] * df['price']
    
    # 2. Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 3. Extract date components
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    # 4. Categorize transactions
    df['transaction_size'] = pd.cut(df['total_amount'], 
                                     bins=[0, 50, 100, 200, float('inf')],
                                     labels=['Small', 'Medium', 'Large', 'XLarge'])
    
    # 5. Add processing metadata
    df['processed_at'] = datetime.now()
    df['processing_batch'] = context['execution_date'].strftime('%Y%m%d_%H%M%S')
    
    # Aggregations for summary statistics
    summary_stats = {
        'total_transactions': len(df),
        'total_revenue': df['total_amount'].sum(),
        'avg_transaction_value': df['total_amount'].mean(),
        'top_product': df.groupby('product')['total_amount'].sum().idxmax(),
        'top_region': df.groupby('region')['total_amount'].sum().idxmax(),
        'processing_date': datetime.now().isoformat()
    }
    
    # Save transformed data
    execution_date = context['execution_date'].strftime('%Y%m%d_%H%M%S')
    transformed_file = PROCESSED_DIR / f'transformed_data_{execution_date}.csv'
    df.to_csv(transformed_file, index=False)
    
    # Save summary statistics
    summary_file = PROCESSED_DIR / f'summary_stats_{execution_date}.json'
    with open(summary_file, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    print(f"Transformed data saved to {transformed_file}")
    print(f"Summary statistics: {summary_stats}")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='transformed_file_path', value=str(transformed_file))
    context['task_instance'].xcom_push(key='summary_stats', value=summary_stats)
    
    return str(transformed_file)


def load_data(**context):
    """
    Load task: Writes processed data to final destination
    In production, this could be:
    - Database INSERT/UPDATE
    - Data warehouse load (Snowflake, BigQuery, Redshift)
    - Write to S3/GCS/Azure Blob
    - Update analytics dashboard
    """
    print("Starting data load...")
    
    # Get file path and stats from previous task
    transformed_file = context['task_instance'].xcom_pull(task_ids='transform', 
                                                           key='transformed_file_path')
    summary_stats = context['task_instance'].xcom_pull(task_ids='transform', 
                                                        key='summary_stats')
    
    # Read transformed data
    df = pd.read_csv(transformed_file)
    
    # Simulate loading to database
    # In production, replace with actual database connection:
    # from sqlalchemy import create_engine
    # engine = create_engine('postgresql://user:password@localhost:5432/dbname')
    # df.to_sql('sales_transactions', engine, if_exists='append', index=False)
    
    # For this example, we'll create a "final" dataset
    final_file = PROCESSED_DIR / 'sales_data_latest.csv'
    df.to_csv(final_file, index=False)
    
    # Create aggregated report
    report = df.groupby(['date', 'region', 'product']).agg({
        'total_amount': ['sum', 'mean', 'count']
    }).round(2)
    
    report_file = PROCESSED_DIR / f'daily_report_{context["execution_date"].strftime("%Y%m%d")}.csv'
    report.to_csv(report_file)
    
    print(f"Loaded {len(df)} records to final destination")
    print(f"Final dataset saved to: {final_file}")
    print(f"Daily report saved to: {report_file}")
    print(f"Summary: {summary_stats}")
    
    return {
        'status': 'success',
        'records_loaded': len(df),
        'total_revenue': summary_stats['total_revenue']
    }


def send_notification(**context):
    """
    Optional: Send notification after pipeline completion
    """
    summary_stats = context['task_instance'].xcom_pull(task_ids='transform', 
                                                        key='summary_stats')
    
    message = f"""
    Batch Pipeline Completed Successfully!
    
    Execution Date: {context['execution_date']}
    Records Processed: {summary_stats['total_transactions']}
    Total Revenue: ${summary_stats['total_revenue']:.2f}
    Average Transaction: ${summary_stats['avg_transaction_value']:.2f}
    Top Product: {summary_stats['top_product']}
    Top Region: {summary_stats['top_region']}
    """
    
    print(message)
    # In production, send email/Slack notification:
    # send_email(to='team@company.com', subject='Pipeline Complete', body=message)
    

# Define default arguments
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# Define the DAG
with DAG(
    dag_id='batch_sales_pipeline',
    default_args=default_args,
    description='Batch processing pipeline for sales data - runs every 2 hours',
    schedule_interval='0 */2 * * *',  # Every 2 hours (cron format)
    start_date=days_ago(1),
    catchup=False,  # Don't run for past dates
    tags=['batch', 'sales', 'etl'],
    max_active_runs=1,  # Only one instance at a time
) as dag:
    
    # Define tasks
    extract_task = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        provide_context=True,
    )
    
    transform_task = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        provide_context=True,
    )
    
    load_task = PythonOperator(
        task_id='load',
        python_callable=load_data,
        provide_context=True,
    )
    
    notify_task = PythonOperator(
        task_id='notify',
        python_callable=send_notification,
        provide_context=True,
    )
    
    # Define task dependencies (pipeline flow)
    extract_task >> transform_task >> load_task >> notify_task