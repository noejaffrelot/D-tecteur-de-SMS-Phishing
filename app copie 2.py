import streamlit as st
import pickle

# =========================
# CONFIG
# =========================
PRICE_EUR = 0.49
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/6oU5kD45VgWr2LUdkL5sA00"

# =========================
# CHARGEMENT MODELE
# =========================
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# =========================
# ETAT DE SESSION
# =========================
if "free_used" not in st.session_state:
    st.session_state.free_used = False

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

if "paid_mode" not in st.session_state:
    st.session_state.paid_mode = False

# =========================
# INTERFACE
# =========================
st.set_page_config(page_title="Détecteur de SMS phishing", page_icon="📱", layout="centered")

st.title("Détecteur de SMS phishing")
st.write("Attention, le détecteur peut se tromper")

st.info("✅ Première analyse gratuite")
st.info(f"💳 Ensuite : {PRICE_EUR:.2f} € par analyse")
st.info("🔐 Code admin : accès sans paiement")

# =========================
# CODE ADMIN
# =========================
admin_code_input = st.text_input("Code admin", type="password")

if admin_code_input:
    if admin_code_input == st.secrets["ADMIN_CODE"]:
        st.session_state.admin_mode = True
        st.success("Mode admin activé.")
    else:
        st.session_state.admin_mode = False
        st.warning("Code admin incorrect.")

# =========================
# MESSAGE UTILISATEUR
# =========================
message = st.text_area("Colle ici le SMS à analyser :")

# =========================
# BOUTON PAYER
# =========================
st.markdown("### Débloquer une analyse payante")

if st.button("Payer 0,49 € avec Stripe"):
    st.markdown(
        f"""
        <meta http-equiv="refresh" content="0; url={STRIPE_PAYMENT_LINK}">
        """,
        unsafe_allow_html=True
    )
    st.link_button("Clique ici si la redirection ne fonctionne pas", STRIPE_PAYMENT_LINK)

# =========================
# BOUTON ANALYSER
# =========================
if st.button("Analyser"):

    if message.strip() == "":
        st.warning("Entre un message avant de lancer l'analyse.")

    elif st.session_state.admin_mode:
        message_vec = vectorizer.transform([message])
        prediction = model.predict(message_vec)[0]
        proba = model.predict_proba(message_vec)[0]

        risque = (1 - proba[model.classes_ == "ham"][0]) * 100

        if prediction == "ham":
            st.success(f"Message probablement sûr — risque phishing : {risque:.2f}%")
        else:
            st.error(f"Message suspect — risque phishing : {risque:.2f}%")

    elif st.session_state.free_used is False:
        message_vec = vectorizer.transform([message])
        prediction = model.predict(message_vec)[0]
        proba = model.predict_proba(message_vec)[0]

        risque = (1 - proba[model.classes_ == "ham"][0]) * 100

        st.session_state.free_used = True

        st.success("🎁 C'était ton analyse gratuite.")

        if prediction == "ham":
            st.success(f"Message probablement sûr — risque phishing : {risque:.2f}%")
        else:
            st.error(f"Message suspect — risque phishing : {risque:.2f}%")

    elif st.session_state.paid_mode:
        message_vec = vectorizer.transform([message])
        prediction = model.predict(message_vec)[0]
        proba = model.predict_proba(message_vec)[0]

        risque = (1 - proba[model.classes_ == "ham"][0]) * 100

        # Une seule analyse payante consommée
        st.session_state.paid_mode = False

        if prediction == "ham":
            st.success(f"Message probablement sûr — risque phishing : {risque:.2f}%")
        else:
            st.error(f"Message suspect — risque phishing : {risque:.2f}%")

    else:
        st.warning("Ta première analyse gratuite a déjà été utilisée.")
        st.warning(f"Pour continuer, paie {PRICE_EUR:.2f} € avec Stripe.")
        st.link_button("Aller vers la page de paiement", STRIPE_PAYMENT_LINK)


if st.button("J'ai payé, débloquer 1 analyse"):
    st.session_state.paid_mode = True
    st.success("1 analyse payante débloquée. Tu peux maintenant cliquer sur Analyser.")
