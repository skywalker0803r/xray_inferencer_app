
# X-Ray Inference Pipeline on AWS

This project is a Minimum Viable Product (MVP) for an automated medical image analysis pipeline using Apache Spark, Apache Airflow, and Docker, deployed on AWS. It demonstrates a scalable and robust architecture for processing large volumes of medical imaging data, aligning with modern MLOps and Data Engineering best practices.

## Architecture Overview

The pipeline consists of the following components orchestrated by Airflow:

1.  **Data Ingestion**: Raw X-ray images are stored in an S3 bucket.
2.  **Spark Preprocessing**: An EMR cluster is used to run a Spark job that preprocesses the images in parallel.
3.  **AI Model Inference**: A Docker container with a pre-trained TorchXRayVision model performs inference on the preprocessed images.
4.  **Orchestration**: An MWAA environment runs an Airflow DAG that defines and manages the entire workflow.

### High-Level Architecture Diagram

```
+-----------------+      +-----------------------+      +----------------------+
|   AWS S3        |----->|   AWS EMR (Spark)     |----->|  AWS ECR             |
| (Raw & Proc.    |      |   (Preprocessing)     |      |  (Docker Image)      |
|  Data)          |      +-----------------------+      +----------------------+
+-----------------+                ^
        |                        |
        |                        |
+--------------------------------v---------------------------------+
|   AWS MWAA (Airflow)                                             |
|                                                                  |
|   +---------------------------+    +-------------------------+   |
|   | SparkSubmitOperator       | >> | DockerOperator          |   |
|   | (Triggers EMR Job)        |    | (Runs Inference)        |   |
|   +---------------------------+    +-------------------------+   |
|                                                                  |
+------------------------------------------------------------------+
```

## Deployment Steps

### 1. Prerequisites

*   An AWS account with appropriate permissions.
*   AWS CLI configured locally.
*   Docker installed locally.
*   Terraform or AWS CloudFormation (optional, for infrastructure as code).

### 2. Build and Push the Docker Image to ECR

First, create an ECR repository to store your inference container image.

```bash
# 1. Create ECR Repository
aws ecr create-repository --repository-name xray-inference-service

# 2. Authenticate Docker to your ECR registry
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com

# 3. Build the Docker image
docker build -t xray-inference-service .

# 4. Tag the image for ECR
docker tag xray-inference-service:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/xray-inference-service:latest

# 5. Push the image to ECR
docker push <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/xray-inference-service:latest
```

### 3. Set up S3 Buckets

Create S3 buckets for your project. You'll need buckets for:

*   **Raw Data**: To store the input X-ray images.
*   **Processed Data**: For Spark to write the preprocessed image data.
*   **Airflow DAGs and Logs**: For your MWAA environment.

### 4. Deploy an EMR Cluster

For the Spark job, you can either use a persistent EMR cluster or create a transient one as part of your Airflow DAG. For this MVP, a simple, long-running cluster is sufficient.

*   Navigate to the EMR console in AWS.
*   Create a cluster with Spark installed.
*   Ensure the cluster's EC2 instance profile has access to the S3 buckets.

### 5. Set up an MWAA Environment

*   Navigate to the MWAA console.
*   Create a new environment, pointing it to the S3 bucket where you will upload your DAGs.
*   Configure the execution role to have permissions for EMR, ECR, and S3.

### 6. Configure Airflow Connections

Once your MWAA environment is running, you need to configure two key connections in the Airflow UI:

*   **`spark_default`**: Configure this to point to your EMR cluster. You will need the master node's DNS name.
*   **`docker_default`**: This connection is used by the `DockerOperator`. Ensure the Airflow workers can access the Docker daemon (this might require custom worker configurations in MWAA).

### 7. Upload Code and DAGs to S3

*   Upload your `dags/` directory, `spark/` directory, and `src/` directory to the S3 bucket that your MWAA environment is configured to use.

## Running the Pipeline

1.  Upload your sample X-ray images to the `raw-data` S3 bucket.
2.  Open the Airflow UI for your MWAA environment.
3.  Find the `xray_inference_pipeline` DAG and trigger it manually.
4.  Monitor the progress of the DAG as it moves from the Spark preprocessing step to the inference step.

## Further Enhancements

This MVP can be extended in several ways:

*   **Monitoring and Logging**: Integrate CloudWatch for detailed logging and monitoring of the pipeline.
*   **Error Handling and Retries**: Implement more sophisticated error handling and retry mechanisms in the Airflow DAG.
*   **CI/CD**: Create a CI/CD pipeline using AWS CodePipeline or GitHub Actions to automate the building and deployment of the Docker image and Airflow DAGs.
*   **Infrastructure as Code**: Use Terraform or CloudFormation to define and manage all the AWS resources, ensuring reproducibility.
*   **Security**: Implement fine-grained IAM roles and security groups to enforce the principle of least privilege.
