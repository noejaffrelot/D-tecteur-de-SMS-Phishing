import streamlit as st
import pickle

# Charger le modèle et le vectorizer
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Titre de l'application
st.title("Détecteur de SMS phishing")

# Zone de texte utilisateur
message = st.text_area("Colle ici le SMS à analyser :")

# Bouton d'analyse
if st.button("Analyser"):
    if message.strip() == "":
        st.warning("Entre un message avant de lancer l'analyse.")
    else:
        message_vec = vectorizer.transform([message])
        prediction = model.predict(message_vec)[0]
        proba = model.predict_proba(message_vec)[0]

        risque = (1 - proba[model.classes_ == "ham"][0]) * 100

        if prediction == "ham":
            st.success(f"Message probablement sûr — risque phishing : {risque:.2f}%")
        else:
            st.error(f"Message suspect — risque phishing : {risque:.2f}%")
