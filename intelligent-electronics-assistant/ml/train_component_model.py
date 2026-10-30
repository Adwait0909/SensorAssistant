"""
Training Script for Component Scanner TensorFlow Model
======================================================

Dataset Directory Structure Required:
-------------------------------------
data/dataset/
├── Arduino/
│   ├── img1.jpg
│   └── img2.jpg
├── ESP32/
├── Raspberry Pi/
├── LED/
├── Resistor/
├── Capacitor/
├── Ultrasonic Sensor/
├── PIR Sensor/
├── LDR/
├── Buzzer/
├── Servo Motor/
├── DC Motor/
├── Relay/
└── Breadboard/

Commands to Train:
------------------
python ml/train_component_model.py
"""

import json
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import layers, models

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data" / "dataset"
MODEL_DIR = BASE_DIR / "ml" / "model"
MODEL_PATH = MODEL_DIR / "component_scanner.keras"
CLASSES_PATH = MODEL_DIR / "classes.json"

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10

def train_component_model():
    print("=" * 60)
    print("TensorFlow Component Scanner Model Trainer")
    print("=" * 60)

    if not DATASET_DIR.exists() or not any(DATASET_DIR.iterdir()):
        print(f"\n[ERROR] Dataset directory not found or empty: {DATASET_DIR}")
        print("\nPlease populate dataset directory following this structure:")
        print("data/dataset/<Class_Name>/<image_files.jpg>")
        print("\nClasses supported:")
        print(" - Arduino, ESP32, Raspberry Pi, LED, Resistor, Capacitor,")
        print(" - Ultrasonic Sensor, PIR Sensor, LDR, Buzzer, Servo Motor,")
        print(" - DC Motor, Relay, Breadboard")
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/4] Loading image dataset from {DATASET_DIR}...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Detected {num_classes} component classes: {class_names}")

    with open(CLASSES_PATH, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)

    # Transfer learning with MobileNetV2 backbone
    print("\n[2/4] Building MobileNetV2 Transfer Learning Architecture...")
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=IMAGE_SIZE + (3,),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=IMAGE_SIZE + (3,))
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs)

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    print("\n[3/4] Training model...")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )

    print(f"\n[4/4] Saving model to {MODEL_PATH}...")
    model.save(str(MODEL_PATH))
    print("[SUCCESS] Component scanner model successfully trained and saved!")

if __name__ == "__main__":
    train_component_model()
