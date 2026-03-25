import pickle
import stripe
import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Détecteur de SMS phishing",
    page_icon="📱",
    layout="centered"
)

PRICE_EUR = 0.49
PRICE_CENTS = 49

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
APP_URL = st.secrets["APP_URL"]

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

if "paid_session_used" not in st.session_state:
    st.session_state.paid_session_used = False

# =========================
# OUTILS
# =========================
def analyse_message(message: str):
    message_vec = vectorizer.transform([message])
    prediction = model.predict(message_vec)[0]
    proba = model.predict_proba(message_vec)[0]

    ham_index = list(model.classes_).index("ham")
    risque = (1 - proba[ham_index]) * 100

    return prediction, risque

def afficher_resultat(prediction, risque):
    if prediction == "ham":
        st.success(f"Message probablement sûr — risque phishing : {risque:.2f}%")
    else:
        st.error(f"Message suspect — risque phishing : {risque:.2f}%")

def create_checkout_session(message: str):
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "unit_amount": PRICE_CENTS,
                    "product_data": {
                        "name": "1 analyse SMS phishing"
                    },
                },
                "quantity": 1,
            }
        ],
        success_url=f"{APP_URL}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}&msg={message}",
        cancel_url=f"{APP_URL}/?payment=cancel",
    )

def get_paid_checkout_session():
    query_params = st.query_params
    payment_status = query_params.get("payment", "")
    session_id = query_params.get("session_id", "")

    if payment_status != "success" or not session_id:
        return None

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            return session
    except Exception:
        return None

    return None

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
# RETOUR DE PAIEMENT STRIPE
# =========================
paid_session = get_paid_checkout_session()

if paid_session and not st.session_state.paid_session_used:
    st.success("Paiement confirmé. Ton analyse payante est débloquée.")

# =========================
# MESSAGE
# =========================
query_params = st.query_params
message_from_url = query_params.get("msg", "")
message = st.text_area("Colle ici le SMS à analyser :", value=message_from_url)

# =========================
# ANALYSE
# =========================
if st.button("Analyser"):

    if message.strip() == "":
        st.warning("Entre un message avant de lancer l'analyse.")

    elif st.session_state.admin_mode:
        prediction, risque = analyse_message(message)
        afficher_resultat(prediction, risque)

    elif st.session_state.free_used is False:
        st.session_state.free_used = True
        prediction, risque = analyse_message(message)
        st.success("🎁 C'était ton analyse gratuite.")
        afficher_resultat(prediction, risque)

    elif paid_session and not st.session_state.paid_session_used:
        st.session_state.paid_session_used = True
        prediction, risque = analyse_message(message)
        afficher_resultat(prediction, risque)
        st.info("Analyse payante consommée.")

        # Nettoie l'URL après usage
        st.query_params.clear()

    else:
        try:
            checkout_session = create_checkout_session(message)

            st.warning("Ta première analyse gratuite a déjà été utilisée.")
            st.link_button("Payer 0,49 € pour continuer", checkout_session.url)

        except Exception as e:
            st.error(f"Erreur Stripe : {e}")
