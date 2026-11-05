# import pandas as pd
# import pickle

# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_absolute_error
# from sklearn.preprocessing import StandardScaler

# from scipy.sparse import hstack

# # Load dataset
# df = pd.read_csv("final_dataset/final_dataset.csv")

# # =========================
# # Features
# # =========================
# X_text = df["components"]

# X_numeric = df[[
#     "has_controller",
#     "has_sensor",
#     "has_output",
#     "has_comm",
#     "component_count"
# ]]

# # Target (numeric score)
# y = df["score_label"]

# # =========================
# # Text → TF-IDF
# # =========================
# vectorizer = TfidfVectorizer(ngram_range=(1, 2))
# X_text_vec = vectorizer.fit_transform(X_text)

# # =========================
# # Scale numeric features
# # =========================
# scaler = StandardScaler()
# X_numeric_scaled = scaler.fit_transform(X_numeric)

# # =========================
# # Combine features
# # =========================
# X_final = hstack([X_text_vec, X_numeric_scaled])

# # =========================
# # Train/Test split
# # =========================
# X_train, X_test, y_train, y_test = train_test_split(
#     X_final, y, test_size=0.2, random_state=42
# )

# # =========================
# # Model
# # =========================
# model = LogisticRegression(max_iter=1000)

# model.fit(X_train, y_train)

# # =========================
# # Evaluation
# # =========================
# y_pred = model.predict(X_test)

# accuracy = model.score(X_test, y_test)
# mae = mean_absolute_error(y_test, y_pred)

# print("Accuracy:", accuracy)
# print("MAE:", mae)

# # =========================
# # Save everything
# # =========================
# pickle.dump(model, open("ml/model.pkl", "wb"))
# pickle.dump(vectorizer, open("ml/vectorizer.pkl", "wb"))
# pickle.dump(scaler, open("ml/scaler.pkl", "wb"))

# print("Model, vectorizer, and scaler saved successfully.")