import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier
import pickle

# Load dataset
df = pd.read_csv("UpdatedResumeDataSet.csv")

# Replace 'label_column' with your target column name
X = df.drop("label_column", axis=1)
y = df["label_column"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train One-vs-Rest SVC model
svc_model = OneVsRestClassifier(SVC())
svc_model.fit(X_train, y_train)

# Save the trained model
with open("clf.pkl", "wb") as f:
    pickle.dump(svc_model, f)

print("Model trained and saved as clf.pkl successfully!")
