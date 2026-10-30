import cv2
import numpy as np
from PIL import Image
import io

IMAGE_SIZE = (224, 224)

def preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    OpenCV & Pillow image preprocessing pipeline.
    1. Decode bytes into Pillow Image
    2. Convert to RGB
    3. Resize to 224x224
    4. Convert to NumPy array
    5. Apply OpenCV Gaussian blurring & histogram normalization
    6. Normalize pixel values to [0.0, 1.0] for TensorFlow model input
    """
    # Load via Pillow
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Convert PIL Image to OpenCV BGR
    open_cv_image = np.array(pil_img)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    # OpenCV Resize
    resized = cv2.resize(open_cv_image, IMAGE_SIZE, interpolation=cv2.INTER_AREA)

    # OpenCV Denoising / Gaussian Blur
    blurred = cv2.GaussianBlur(resized, (3, 3), 0)

    # Convert back to RGB for Keras/TensorFlow model
    rgb_img = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)

    # Normalize pixels [0, 1]
    normalized = rgb_img.astype(np.float32) / 255.0
    
    # Expand dims to shape (1, 224, 224, 3)
    return np.expand_dims(normalized, axis=0)
