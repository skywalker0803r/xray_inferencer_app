
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies required for pyspark and other libraries
RUN apt-get update && apt-get install -y     default-jre     && apt-get clean

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY src/ ./src
COPY data/ ./data

# Define the command to run the application
CMD ["python", "src/inference.py"]

