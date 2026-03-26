import streamlit as st
import pickle
import stripe

# =========================
# CONFIG
# =========================
PRICE_EUR = 0.49
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/6oU5kD45VgWr2LUdkL5sA00"

st.set_page_config(
    page_title="Détecteur de SMS phishing",
    page_icon="📱",
    layout="centered"
)

# Stripe secret key
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

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

if "used_checkout_sessions" not in st.session_state:
    st.session_state.used_checkout_sessions = set()

# =========================
# FONCTIONS
# =========================
def analyser_message(message: str):
    message_vec = vectorizer.transform([message])
    prediction = model.predict(message_vec)[0]
    proba = model.predict_proba(message_vec)[0]

    # Probabilité que ce soit du phishing
    ham_index = list(model.classes_).index("ham")
    risque = (1 - proba[ham_index]) * 100

    if prediction == "ham":
        st.success(f"Message probablement sûr — risque phishing : {risque:.2f}%")
    else:
        st.error(f"Message suspect — risque phishing : {risque:.2f}%")

def verifier_paiement_stripe():
    """
    Vérifie si Stripe a renvoyé un checkout_session_id valide et payé.
    Débloque 1 analyse si paiement confirmé.
    """
    session_id = st.query_params.get("checkout_session_id")

    if not session_id:
        return

    # Évite de redébloquer plusieurs fois la même session Stripe
    if session_id in st.session_state.used_checkout_sessions:
        return

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # On ne débloque que si le paiement est réellement payé
        if checkout_session.payment_status == "paid":
            st.session_state.paid_mode = True
            st.session_state.used_checkout_sessions.add(session_id)
            st.success("Paiement confirmé. 1 analyse payante a été débloquée.")
        else:
            st.warning("Le paiement n'est pas encore confirmé par Stripe.")

    except Exception as e:
        st.error(f"Impossible de vérifier le paiement Stripe : {e}")

# =========================
# VERIFICATION PAIEMENT AU RETOUR DE STRIPE
# =========================
verifier_paiement_stripe()

# =========================
# INTERFACE
# =========================
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
st.link_button(f"Payer {PRICE_EUR:.2f} € avec Stripe", STRIPE_PAYMENT_LINK)

# =========================
# BOUTON ANALYSER
# =========================
if st.button("Analyser"):

    if message.strip() == "":
        st.warning("Entre un message avant de lancer l'analyse.")

    elif st.session_state.admin_mode:
        analyser_message(message)

    elif st.session_state.free_used is False:
        st.session_state.free_used = True
        st.success("🎁 C'était ton analyse gratuite.")
        analyser_message(message)

    elif st.session_state.paid_mode:
        analyser_message(message)
        # Consomme l'analyse payante
        st.session_state.paid_mode = False

    else:
        st.warning("Ta première analyse gratuite a déjà été utilisée.")
        st.warning(f"Pour continuer, paie {PRICE_EUR:.2f} € avec Stripe.")
        st.link_button("Aller vers la page de paiement", STRIPE_PAYMENT_LINK)
