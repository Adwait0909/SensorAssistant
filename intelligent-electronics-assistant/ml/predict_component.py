import os
import io
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

from services.component_service import ComponentService
from services.gemini_vision_service import GeminiVisionService
from config import Config

logger = logging.getLogger("ElectronicsAssistant")

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "ml" / "model"
MODEL_PKL_PATH = MODEL_DIR / "component_classifier.pkl"
MODEL_KERAS_PATH = MODEL_DIR / "component_scanner.keras"
CLASSES_PATH = MODEL_DIR / "classes.json"

# Common local-model classes. Gemini is not restricted to this catalogue.
SUPPORTED_CLASSES = [
    "Arduino Uno", "ESP32", "Raspberry Pi", "LED", "Resistor",
    "Capacitor", "Ultrasonic Sensor", "PIR Sensor", "LDR",
    "Buzzer", "Servo Motor", "DC Motor", "Relay", "Breadboard",
    "MQ-2 Gas Sensor", "DHT11 Sensor", "LCD 16x2", "Push Button"
]

CATEGORY_MAP = {
    "Arduino Uno": "Controllers",
    "Arduino": "Controllers",
    "ESP32": "Controllers",
    "Raspberry Pi": "Controllers",
    "LED": "Outputs",
    "Buzzer": "Outputs",
    "Servo Motor": "Outputs",
    "DC Motor": "Outputs",
    "Relay": "Outputs",
    "LCD 16x2": "Outputs",
    "Ultrasonic Sensor": "Sensors",
    "PIR Sensor": "Sensors",
    "LDR": "Sensors",
    "MQ-2 Gas Sensor": "Sensors",
    "DHT11 Sensor": "Sensors",
    "Resistor": "Supporting components",
    "Capacitor": "Supporting components",
    "Breadboard": "Supporting components",
    "Push Button": "Input components"
}

class ComponentScannerPredictor:
    _pkl_bundle = None
    _keras_model = None
    _classes = None
    _is_loaded = False

    @classmethod
    def load_model_if_exists(cls) -> bool:
        """Lazy loader for trained vision classifier models."""
        if cls._is_loaded:
            return cls._pkl_bundle is not None or cls._keras_model is not None

        # Prefer the image model. The PKL model uses generic color/edge features
        # and cannot reliably identify components from photographs.
        if MODEL_KERAS_PATH.exists():
            try:
                    import tensorflow as tf
                    cls._keras_model = tf.keras.models.load_model(str(MODEL_KERAS_PATH))
                    if CLASSES_PATH.exists():
                        with open(CLASSES_PATH, "r", encoding="utf-8") as f:
                            cls._classes = json.load(f)
                    else:
                        cls._classes = SUPPORTED_CLASSES
                    cls._is_loaded = True
                    logger.info(f"Loaded TensorFlow Component Scanner model from {MODEL_KERAS_PATH}")
                    return True
            except Exception as e:
                    logger.error(f"Failed to load Keras model: {e}")

        # Do not use the legacy PKL model as an image classifier.
        if MODEL_PKL_PATH.exists():
            try:
                    with open(MODEL_PKL_PATH, "rb") as f:
                        bundle = pickle.load(f)
                    if isinstance(bundle, dict) and "profiles" in bundle:
                        logger.warning("Ignoring legacy feature-only component classifier; an image model is required.")
            except Exception as e:
                    logger.error(f"Failed to inspect legacy PKL model: {e}")

        cls._is_loaded = True
        return cls._pkl_bundle is not None or cls._keras_model is not None

    @classmethod
    def is_model_available(cls) -> bool:
        return cls.load_model_if_exists() or GeminiVisionService.is_available()

    @classmethod
    def _extract_image_features(cls, image_bytes: bytes) -> np.ndarray:
        """Extract multi-modal visual descriptors (Color, Texture, Geometry, Contours) via PIL & OpenCV."""
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = pil_img.size
        aspect_ratio = float(w) / float(max(1, h))

        img_np = np.array(pil_img)
        
        if cv2 is not None:
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            mean_hue = float(np.mean(hsv[:, :, 0])) / 180.0
            mean_sat = float(np.mean(hsv[:, :, 1])) / 255.0
            mean_val = float(np.mean(hsv[:, :, 2])) / 255.0

            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = float(np.count_nonzero(edges)) / float(edges.size)

            # Contours and rectangularity
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                max_cnt = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(max_cnt)
                x, y, bw, bh = cv2.boundingRect(max_cnt)
                rect_ratio = float(area) / float(max(1, bw * bh))
            else:
                rect_ratio = 0.5
        else:
            mean_hue, mean_sat, mean_val = 0.5, 0.5, 0.5
            edge_density, rect_ratio = 0.3, 0.5

        features = [
            mean_hue,
            mean_sat,
            mean_val,
            edge_density,
            min(10.0, aspect_ratio),
            rect_ratio,
            float(np.mean(img_np[:, :, 0])) / 255.0,
            float(np.mean(img_np[:, :, 2])) / 255.0
        ]
        return np.array(features).reshape(1, -1)

    @classmethod
    def predict(cls, image_bytes: bytes) -> Dict[str, Any]:
        """
        Run classification pipeline with trained model and vision feature extraction.
        """
        cls.load_model_if_exists()

        try:
            if Config.GEMINI_API_KEY:
                result = GeminiVisionService.identify_component(image_bytes)
                component = result.get("component")
                if component:
                    normalized_name = ComponentService.normalize_name(component)
                    result["normalized_name"] = normalized_name
                    result["category"] = CATEGORY_MAP.get(
                        component, CATEGORY_MAP.get(normalized_name, result.get("category", "Sensors"))
                    )
                else:
                    result["normalized_name"] = None
                return result

            if cls._keras_model is None:
                return {
                    "model_available": False,
                    "component": None,
                    "normalized_name": None,
                    "category": None,
                    "confidence": 0.0,
                    "message": "Model not trained. Upload a trained model or run the training script. Add labeled component images before training."
                }

            feats = cls._extract_image_features(image_bytes)

            if cls._keras_model is not None:
                from ml.preprocess import preprocess_image_bytes
                processed_img = preprocess_image_bytes(image_bytes)
                preds = cls._keras_model.predict(processed_img, verbose=0)[0]
                top_idx = int(preds.argmax())
                confidence = round(float(preds[top_idx]) * 100.0, 1)
                classes = cls._classes or SUPPORTED_CLASSES
                if top_idx >= len(classes):
                    raise ValueError("Image model output does not match the stored class labels.")
                detected_class = classes[top_idx]

            normalized_name = ComponentService.normalize_name(detected_class)
            category = CATEGORY_MAP.get(
                detected_class,
                CATEGORY_MAP.get(normalized_name, "Electronic component")
            )

            return {
                "model_available": True,
                "component": detected_class,
                "normalized_name": normalized_name,
                "category": category,
                "confidence": confidence,
                "is_sensor": category == "Sensors",
                "message": f"Successfully identified {normalized_name} ({category}) with {confidence}% AI confidence."
            }

        except (ValueError, OSError, TypeError, KeyError, IndexError) as e:
            logger.error(f"Prediction error: {e}")
            return {
                "model_available": cls._keras_model is not None,
                "component": None,
                "normalized_name": None,
                "category": None,
                "confidence": 0.0,
                "is_sensor": False,
                "message": "The image could not be classified. Use a clear, well-lit image showing one component and try again."
            }
