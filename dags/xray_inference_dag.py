
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# --- Constants --- #
# Replace these with your actual AWS resource names and S3 paths
S3_BUCKET = "your-s3-bucket-name" # e.g., "my-xray-pipeline-bucket"
RAW_DATA_S3_PATH = f"s3://{S3_BUCKET}/raw-data/"
PROCESSED_DATA_S3_PATH = f"s3://{S3_BUCKET}/processed-data/"
SPARK_SCRIPT_S3_PATH = f"s3://{S3_BUCKET}/spark/preprocess.py"

ECS_CLUSTER_NAME = "your-ecs-cluster-name" # e.g., "xray-inference-cluster"
ECS_TASK_DEFINITION = "your-ecs-task-definition-name" # e.g., "xray-inference-task:1"
ECS_CONTAINER_NAME = "your-container-name-in-task-definition" # e.g., "xray-inference-service"

with DAG(
    dag_id="production_xray_inference_pipeline",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,  # This DAG is manually triggered
    tags=["xray", "inference", "spark", "aws", "production"],
) as dag:
    
    # Task to run the Spark preprocessing job on EMR
    # This task reads from raw S3, processes, and writes to processed S3.
    run_spark_preprocessing = SparkSubmitOperator(
        task_id="run_spark_preprocessing",
        application=SPARK_SCRIPT_S3_PATH,
        conn_id="emr_default",  # Assumes an EMR connection is configured in Airflow
        verbose=True,
        # Pass input and output paths to the Spark script
        application_args=[
            RAW_DATA_S3_PATH,
            PROCESSED_DATA_S3_PATH
        ],
        # This allows the next task to pull the output path
        do_xcom_push=True,
    )

    # Task to run inference using an ECS Fargate task.
    # This is a placeholder for a more complex logic that would iterate over
    # all processed files. For this example, we assume the Spark job outputs
    # a single, representative file path or we take the first one.
    run_xray_inference_on_ecs = EcsRunTaskOperator(
        task_id="run_xray_inference_on_ecs",
        aws_conn_id="aws_default", # Assumes an AWS connection is configured
        cluster=ECS_CLUSTER_NAME,
        task_definition=ECS_TASK_DEFINITION,
        launch_type="FARGATE",
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": ["your-subnet-id-1", "your-subnet-id-2"], # Replace with your VPC subnets
                "securityGroups": ["your-security-group-id"], # Replace with your security group
                "assignPublicIp": "ENABLED",
            },
        },
        # Override the container command to pass the S3 path dynamically
        overrides={
            "containerOverrides": [
                {
                    "name": ECS_CONTAINER_NAME,
                    # This pulls the output from the Spark task.
                    # NOTE: This is a simplified example. SparkSubmitOperator doesn't directly push a usable path.
                    # A more robust solution would involve an intermediate S3 sensor or a Lambda function
                    # to list the files in the output directory and trigger inference for each.
                    # For this example, we'll pretend we can construct the path.
                    "command": [
                        "python", 
                        "src/inference.py", 
                        "--image_path", 
                        f"{RAW_DATA_S3_PATH}xray.jpg" # Placeholder: replace with dynamic XCom pull
                    ],
                },
            ],
        },
    )

    # Set the task dependency
    run_spark_preprocessing >> run_xray_inference_on_ecs
