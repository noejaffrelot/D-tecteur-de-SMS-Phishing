import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# 1 charger le dataset
df = pd.read_csv("sms_dataset_advanced_fr_en.csv")

# 2 définir X et y
X = df["text"]
y = df["label"]

# 3 train / test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4 vectorisation TF-IDF
vectorizer = TfidfVectorizer()

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 5 modèle
model = MultinomialNB()

# 6 entraînement
model.fit(X_train_vec, y_train)

# 7 sauvegarde
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Modèle et vectorizer sauvegardés avec succès.")
