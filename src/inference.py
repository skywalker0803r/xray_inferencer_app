import torch
import torchvision
import torchxrayvision as xrv
import skimage.io
import numpy as np
import argparse
import boto3
import os
from urllib.parse import urlparse

def download_from_s3(s3_path: str, local_dir: str = "/tmp/data") -> str:
    """
    Downloads a file from an S3 path to a local directory.
    """
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    parsed_url = urlparse(s3_path)
    bucket_name = parsed_url.netloc
    object_key = parsed_url.path.lstrip('/')
    
    file_name = os.path.basename(object_key)
    local_path = os.path.join(local_dir, file_name)
    
    s3 = boto3.client('s3')
    print(f"Downloading s3://{bucket_name}/{object_key} to {local_path}")
    s3.download_file(bucket_name, object_key, local_path)
    return local_path

def run_inference(image_path: str) -> dict:
    """
    Runs the TorchXRayVision inference on a single image.

    Args:
        image_path: Path to the input image file.

    Returns:
        A dictionary with pathologies and their predicted probabilities.
    """
    model_name = "densenet121-res224-rsna"
    model = xrv.models.get_model(model_name)
    
    img = skimage.io.imread(image_path)
    img = xrv.datasets.normalize(img, 255)

    # Check that images are 2D arrays
    if len(img.shape) > 2:
        img = img[:, :, 0]
    if len(img.shape) < 2:
        raise ValueError("Image dimension is less than 2.")

    # Add color channel
    img = img[None, :, :]
    
    transform = torchvision.transforms.Compose([xrv.datasets.XRayCenterCrop()])
    img = transform(img)

    with torch.no_grad():
        img = torch.from_numpy(img).unsqueeze(0)
        preds = model(img).cpu()
        output = {
            k: float(v)
            for k, v in zip(xrv.datasets.default_pathologies, preds[0].detach().numpy())
        }
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run X-Ray inference on an image from S3.")
    parser.add_argument("--image_path", type=str, required=True, help="The S3 path to the image (e.g., s3://bucket/key.jpg)")
    args = parser.parse_args()

    # Download the image from S3 to a temporary local path
    try:
        local_image_path = download_from_s3(args.image_path)
        results = run_inference(local_image_path)
        print("Inference Results:")
        print(results)
    except Exception as e:
        print(f"An error occurred: {e}")
        # Clean up the downloaded file if it exists
        if 'local_image_path' in locals() and os.path.exists(local_image_path):
            os.remove(local_image_path)