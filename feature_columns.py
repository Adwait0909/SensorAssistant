import pandas as pd
import json

df = pd.read_csv("iot_dataset_balanced.csv")

features = df.drop(columns=["score_label", "project_type", "difficulty"]).columns.tolist()

with open("ml/feature_columns.json", "w") as f:
    json.dump(features, f)

print("feature_columns.json created")