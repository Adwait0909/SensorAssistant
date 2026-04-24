import pandas as pd
from sklearn.utils import resample

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("iot_dataset_clean.csv")

print("Original distribution:")
print(df["project_type"].value_counts())

# =========================
# SPLIT BY CLASS
# =========================
groups = df.groupby("project_type")

# find majority class size
max_size = df["project_type"].value_counts().max()

balanced_list = []

# =========================
# OVERSAMPLING LOOP
# =========================
for name, group in groups:
    df_resampled = resample(
        group,
        replace=True,           # KEY: allows duplication
        n_samples=max_size,     # match majority class
        random_state=42
    )
    balanced_list.append(df_resampled)

# =========================
# MERGE BACK
# =========================
balanced_df = pd.concat(balanced_list)

# shuffle dataset (important)
balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)

# =========================
# CHECK RESULT
# =========================
print("\nBalanced distribution:")
print(balanced_df["project_type"].value_counts())

# =========================
# SAVE DATASET
# =========================
balanced_df.to_csv("iot_dataset_balanced.csv", index=False)

print("\nSaved: iot_dataset_balanced.csv")