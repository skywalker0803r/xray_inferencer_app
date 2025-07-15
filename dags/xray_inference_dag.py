from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="xray_inference_pipeline",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,  # This DAG is manually triggered
    tags=["xray", "inference", "spark"],
) as dag:
    
    # Task to run the Spark preprocessing job
    # In a real AWS environment, you would configure the connection to your EMR cluster
    # and the application file (preprocess.py) would be located in S3.
    run_spark_preprocessing = SparkSubmitOperator(
        task_id="run_spark_preprocessing",
        application="spark/preprocess.py", # Path to the Spark script
        conn_id="spark_default", # Assumes a Spark connection is configured in Airflow
        verbose=True,
    )

    # Task to run the inference using the Docker image
    # This task will run after the Spark preprocessing is complete
    run_xray_inference = DockerOperator(
        task_id="run_xray_inference",
        image="xray-inference-service:latest",
        command="python src/inference.py",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        auto_remove=True,
    )

    # Set the task dependency
    run_spark_preprocessing >> run_xray_inference