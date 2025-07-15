
import torch
import torchvision
import torchxrayvision as xrv
import skimage.io
import numpy as np

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
    # This allows the script to be run directly for testing
    # We will download the image to the data directory
    import urllib.request
    import os

    if not os.path.exists("data"):
        os.makedirs("data")

    img_url = "https://huggingface.co/spaces/torchxrayvision/torchxrayvision-classifier/resolve/main/16747_3_1.jpg"
    img_path = "data/xray.jpg"
    
    if not os.path.exists(img_path):
        urllib.request.urlretrieve(img_url, img_path)
    
    results = run_inference(img_path)
    print(results)
