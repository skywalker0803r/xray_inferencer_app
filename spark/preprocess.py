from pyspark.sql import SparkSession
from pyspark.sql.functions import col, element_at, split
import sys

def main():
    """
    Main Spark job function.
    Reads images from an input S3 path, simulates preprocessing,
    and writes the results to an output S3 path.
    """
    if len(sys.argv) != 3:
        print("Usage: spark-submit preprocess.py <input_s3_path> <output_s3_path>")
        sys.exit(-1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    spark = SparkSession.builder.appName("XRayPreprocessing").getOrCreate()

    # Read image data from S3. "binaryFile" format reads the whole file.
    # This loads the data into a DataFrame with columns:
    # path, modificationTime, length, content
    raw_images_df = spark.read.format("binaryFile").load(input_path)

    # Simulate preprocessing: for this example, we'll just rename the files
    # and assume they are "processed". In a real scenario, a UDF would be
    # applied here to transform the 'content' column.
    # We extract the original filename to create a new "processed" path.
    processed_df = raw_images_df.withColumn(
        "filename", element_at(split(col("path"), "/"), -1)
    ).withColumn(
        "processed_image_path", col("path") # In a real scenario, this would be the new S3 path
    )

    print(f"Successfully processed images from {input_path}.")
    processed_df.show(truncate=False)

    # Write the DataFrame with processed image paths to the output location
    # The next task in Airflow will read from this location.
    # We select only the path to be saved.
    final_df = processed_df.select("processed_image_path")
    final_df.write.mode("overwrite").format("parquet").save(output_path)
    
    print(f"Wrote processed data manifest to {output_path}.")

    spark.stop()

if __name__ == "__main__":
    main()