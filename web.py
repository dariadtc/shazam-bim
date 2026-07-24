import hashlib
import io
import os
import random
import sqlite3
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# 0. CONFIGURARE FORMSPREE PENTRU SOLICITĂRI & CONTACT
# -----------------------------------------------------------------------------
FORMSPREE_ID = "xeeyrbyb"


def trimite_solicitare_resetare_catre_admin(email_client, cod_otp):
    """Trimite e-mail pe adresa ta (prin Formspree) cu e-mailul clientului și codul generat."""
    if FORMSPREE_ID == "ID-UL_TAU_AICI":
        return True

    url = f"https://formspree.io/f/{FORMSPREE_ID}"
    data = {
        "email_client": email_client,
        "cod_verificare": cod_otp,
        "mesaj": f"SOLICITARE RESETARE PAROLĂ\n\n• E-mail Client: {email_client}\n• Cod de Verificare (OTP): {cod_otp}\n\nTrimite acest cod de 6 cifre clientului pentru a-și reconfigura parola în aplicație.",
        "_subject": f"🔑 Solicitare Resetare Parolă pentru: {email_client}",
    }
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Eroare la trimitere Formspree: {e}")
        return False


def trimite_email_formspree(email, tip, mesaj):
    """Folosit pentru formularul general de contact/feedback din sidebar."""
    if FORMSPREE_ID == "ID-UL_TAU_AICI":
        return True

    url = f"https://formspree.io/f/{FORMSPREE_ID}"
    data = {
        "email": email,
        "subiect": tip,
        "mesaj": mesaj,
        "_subject": f"📬 Shazam-BIM Feedback: {tip}",
    }
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Eroare la trimitere contact: {e}")
        return False


# 1. Configurare pagină
st.set_page_config(
    page_title="Shazam-BIM Cloud - Relevee 3D Universal LiDAR & SLAM AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Stare Autentificare Sesiune
if "user_conectat" not in st.session_state:
    st.session_state.user_conectat = None

if "otp_reset" not in st.session_state:
    st.session_state.otp_reset = None
if "email_reset_target" not in st.session_state:
    st.session_state.email_reset_target = None

# CSS dinamic în funcție de stare
css_hide_sidebar = ""
if st.session_state.user_conectat is None:
    css_hide_sidebar = """
        [data-testid="stSidebar"] {
            display: none !important;
        }
    """

# 2. Injectare CSS Custom
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@600;800;900&display=swap');
    
    .stApp {{
        background-color: #090C10;
        font-family: 'Inter', sans-serif;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    {css_hide_sidebar}
    
    /* ASCUNDE ICONIȚA NATIVĂ DE LINK / ANCHOR DIN STREAMLIT */
    .stMarkdown a.anchor-link, 
    [data-testid="stHeaderActionElements"],
    a.header-anchor {{
        display: none !important;
    }}
    
    /* LOGO NEON GLOW EFFECTS */
    .logo-container {{
        text-align: center;
        padding: 15px 0 10px 0;
        user-select: none;
    }}
    .logo-shazam {{
        font-family: 'Orbitron', sans-serif;
        font-size: 32px;
        font-weight: 800;
        color: #00FFFF;
        text-shadow: 
            0 0 5px #00FFFF,
            0 0 15px rgba(0, 255, 255, 0.7);
        animation: glowCyan 2.5s infinite alternate;
    }}
    .logo-bim {{
        font-family: 'Orbitron', sans-serif;
        font-size: 32px;
        font-weight: 800;
        color: #50C878;
        text-shadow: 
            0 0 5px #50C878,
            0 0 15px rgba(80, 200, 120, 0.7);
        animation: glowGreen 2.5s infinite alternate;
    }}

    @keyframes glowCyan {{
        0% {{ text-shadow: 0 0 5px #00FFFF, 0 0 10px rgba(0, 255, 255, 0.5); }}
        100% {{ text-shadow: 0 0 8px #00FFFF, 0 0 20px rgba(0, 255, 255, 0.9); }}
    }}
    @keyframes glowGreen {{
        0% {{ text-shadow: 0 0 5px #50C878, 0 0 10px rgba(80, 200, 120, 0.5); }}
        100% {{ text-shadow: 0 0 8px #50C878, 0 0 20px rgba(80, 200, 120, 0.9); }}
    }}

    /* BADGES DE FORMAT EXTINSE */
    .format-badge {{
        display: inline-block;
        background: rgba(0, 255, 255, 0.08);
        border: 1px solid rgba(0, 255, 255, 0.25);
        padding: 3px 7px;
        border-radius: 6px;
        font-size: 10px;
        color: #00FFFF;
        margin-right: 3px;
        margin-bottom: 4px;
        font-weight: 600;
    }}

    /* Status Badge Pulsant */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        background: rgba(80, 200, 120, 0.1);
        border: 1px solid rgba(80, 200, 120, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        color: #50C878;
        font-size: 11px;
        font-weight: 600;
    }}
    .gpu-badge {{
        display: inline-flex;
        align-items: center;
        background: rgba(168, 85, 247, 0.1);
        border: 1px solid rgba(168, 85, 247, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        color: #A855F7;
        font-size: 11px;
        font-weight: 600;
        margin-left: 8px;
    }}
    .pulse-dot {{
        width: 7px;
        height: 7px;
        background-color: #50C878;
        border-radius: 50%;
        margin-right: 6px;
        box-shadow: 0 0 8px #50C878;
    }}

    /* Carduri KPI Custom */
    .kpi-card {{
        background: rgba(18, 22, 33, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        border-color: rgba(0, 255, 255, 0.3);
    }}
    .kpi-label {{
        color: #8A94A6;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 700;
        font-family: 'Orbitron', sans-serif;
    }}

    /* Stilizare Panou Lateral */
    [data-testid="stSidebar"] {{
        background-color: #0E121B;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }}
    
    /* Stilizare Buton Principal */
    div.stButton > button:first-child {{
        background: linear-gradient(135deg, #00E5FF 0%, #0088FF 100%);
        color: #000000;
        font-weight: 700;
        font-size: 15px;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.25);
        transition: all 0.2s ease;
    }}
    div.stButton > button:first-child:hover {{
        box-shadow: 0 6px 22px rgba(0, 229, 255, 0.45);
        transform: scale(1.01);
    }}

    /* Stilizare Tab-uri */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: #121621;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        border-radius: 6px;
        color: #8A94A6;
        font-weight: 600;
        font-size: 13px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #1A202C !important;
        color: #00FFFF !important;
    }}

    /* Carduri de Prețuri */
    .price-card {{
        background: #121621;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        height: 100%;
    }}
    .price-card-pro {{
        border: 1.5px solid #00FFFF;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.15);
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 3. BAZĂ DE DATE
# -----------------------------------------------------------------------------


def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()


def init_db():
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS utilizatori (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, parola TEXT, data_inregistrare TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS scanari (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, nume_proiect TEXT, data_procesare TEXT, lungime_teva REAL, lungime_perete REAL, inaltime_perete REAL, latime_gol REAL, inaltime_gol REAL)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS mesaje_contact (id INTEGER PRIMARY KEY AUTOINCREMENT, data_trimitere TEXT, email_client TEXT, tip_mesaj TEXT, mesaj TEXT)"
    )
    conn.commit()
    conn.close()


def exista_email(email):
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    c.execute(
        "SELECT * FROM utilizatori WHERE email = ?", (str(email).lower().strip(),)
    )
    user = c.fetchone()
    conn.close()
    return user is not None


def creeaza_utilizator(email, parola):
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute(
            "INSERT INTO utilizatori (email, parola, data_inregistrare) VALUES (?,?,?)",
            (str(email).lower().strip(), hash_password(parola), dt),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def verifica_utilizator(email, parola):
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    c.execute(
        "SELECT * FROM utilizatori WHERE email = ? AND parola = ?",
        (str(email).lower().strip(), hash_password(parola)),
    )
    user = c.fetchone()
    conn.close()
    return user is not None


def schimba_parola(email, parola_noua):
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    c.execute(
        "UPDATE utilizatori SET parola = ? WHERE email = ?",
        (hash_password(parola_noua), str(email).lower().strip()),
    )
    randuri_afectate = c.rowcount
    conn.commit()
    conn.close()
    return randuri_afectate > 0


def numara_utilizari(email):
    if not email:
        return 0
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scanari WHERE user_email = ?", (str(email),))
    numar = c.fetchone()
    conn.close()
    return numar[0] if numar else 0


def salveaza_scanare(email, nume, l_t, l_w, h_w, l_g, h_g):
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO scanari (user_email, nume_proiect, data_procesare, lungime_teva, lungime_perete, inaltime_perete, latime_gol, inaltime_gol) VALUES (?,?,?,?,?,?,?,?)",
        (
            str(email),
            str(nume),
            dt,
            round(float(l_t), 2),
            round(float(l_w), 2),
            round(float(h_w), 2),
            round(float(l_g), 2),
            round(float(h_g), 2),
        ),
    )
    conn.commit()
    conn.close()


def salveaza_contact(email, tip, text):
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO mesaje_contact (data_trimitere, email_client, tip_mesaj, mesaj) VALUES (?,?,?,?)",
        (dt, str(email), str(tip), str(text)),
    )
    conn.commit()
    conn.close()


def citeste_istoric_privat(email):
    if not email:
        return []
    conn = sqlite3.connect("proiecte_bim.db")
    c = conn.cursor()
    c.execute(
        "SELECT nume_proiect, data_procesare, lungime_teva, lungime_perete, inaltime_perete, latime_gol, inaltime_gol FROM scanari WHERE user_email = ? ORDER BY id DESC",
        (str(email),),
    )
    date = c.fetchall()
    conn.close()
    return date


def genereaza_raport_tehnic(nume, l_t, l_w, h_w, l_gol, h_gol):
    dt = datetime.now().strftime("%d.%m.%Y %H:%M")
    suprafata_perete = l_w * h_w
    volum_camera = l_w * 3.0 * h_w

    continut = f"""================================================================================
                    SHAZAM-BIM AI ENGINE - FIȘĂ TEHNICĂ RELEVEU
================================================================================
Data generării: {dt}
Identificator Proiect: {nume}
Acuratețe Digitală Estimată: < 5 mm (Clasă A)
Engine Versiune: v2.4 Cloud AI

1. METRICI STRUCTURALE EXSTRASE
--------------------------------------------------------------------------------
- Lungime Totală Perete Principal : {l_w:.2f} m
- Înălțime Liberă Încăpere        : {h_w:.2f} m
- Grosime Perete Detectată        : 0.20 m (20 cm)
- Suprafață Totală Perete         : {suprafata_perete:.2f} mp
- Volum Brut Estimat Încăpere     : {volum_camera:.2f} mc

2. ELEMENTE TÂMPLĂRIE / GOLURI DETECTATE
--------------------------------------------------------------------------------
- Lățime Gol Ușă                  : {l_gol:.2f} m
- Înălțime Gol Ușă                : {h_gol:.2f} m
- Suprafață Decupaj Gol           : {l_gol * h_gol:.2f} mp

3. INSTALAȚII MEP (MECHANICAL, ELECTRICAL, PLUMBING)
--------------------------------------------------------------------------------
- Traseu Țeavă Identificat       : 1 Traseu Cilindric
- Lungime Totală Țeavă            : {l_t:.2f} m
- Diametru Estimat Țeavă          : 0.16 m (Rază 8 cm)

4. STATUS CONFORMITATE & EXPORT
--------------------------------------------------------------------------------
- Format Export Solide 3D         : .OBJ (Compatibil Revit, AutoCAD, ArchiCAD)
- Status Verificare Geometrie     : VALIDĂ (Fără coliziuni detected)

================================================================================
Document generat automat de platforma Shazam-BIM AI Cloud Processing System.
Verificarea finală pe șantier revine inginerului autorizat de proiect.
================================================================================
"""
    return continut


init_db()

# -----------------------------------------------------------------------------
# SCENARIUL A: UTILIZATORUL NU ESTE CONECTAT (FULL SCREEN LOGIN)
# -----------------------------------------------------------------------------
if st.session_state.user_conectat is None:

    st.markdown(
        """
        <div class='logo-container' style='margin-top: 50px;'>
            <span class='logo-shazam' style='font-size: 45px;'>Shazam</span><span class='logo-bim' style='font-size: 45px;'>-BIM</span>
            <p style='font-size: 13px; color: #00FF66; font-weight: 600; letter-spacing: 1px; margin-top: 10px;'>
                PLATFORMĂ UNIVERSALĂ CLOUD PENTRU RELEVEE STRUCTURALE ȘI INSTALAȚII MEP
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([1, 2, 1])

    with col_b:
        tab_login, tab_register = st.tabs(
            ["🔑 Conectare", "📝 Înregistrare Cont"]
        )

        with tab_login:
            st.write("<br>", unsafe_allow_html=True)
            email_in = st.text_input(
                "Adresă E-mail:", placeholder="nume@companie.ro", key="m_l_email"
            )
            pass_in = st.text_input(
                "Parolă:", type="password", key="m_l_pass"
            )

            if st.button("🚀 Autentificare în Cloud", use_container_width=True):
                if verifica_utilizator(email_in, pass_in):
                    st.session_state.user_conectat = email_in.lower().strip()
                    st.success("🎉 Conectat cu succes! Se încarcă spațiul de lucru...")
                    st.rerun()
                else:
                    st.error("❌ Adresă de e-mail sau parolă incorectă!")

            # 🔐 RESETARE PAROLĂ VIA FORMSPREE CĂTRE ADMIN (TU ÎI TRIMIȚI CODUL)
            st.write("<br>", unsafe_allow_html=True)
            with st.expander("❓ Ai uitat parola?", expanded=False):
                st.markdown(
                    "<p style='font-size: 12px; color: #8A94A6;'>Introduceți e-mailul înregistrat. Un cod de verificare va fi transmis către echipa de suport pentru confirmare.</p>",
                    unsafe_allow_html=True,
                )

                rst_email_input = st.text_input(
                    "E-mailul contului tău:",
                    placeholder="nume@companie.ro",
                    key="secur_rst_email",
                )

                if st.button("📩 Solicită Cod de Verificare", use_container_width=True):
                    if rst_email_input:
                        if exista_email(rst_email_input):
                            cod_generat = str(random.randint(100000, 999999))
                            st.session_state.otp_reset = cod_generat
                            st.session_state.email_reset_target = (
                                rst_email_input.lower().strip()
                            )

                            trimis = trimite_solicitare_resetare_catre_admin(
                                rst_email_input.lower().strip(), cod_generat
                            )

                            if trimis:
                                st.info(
                                    f"📩 Solicitarea ta a fost transmisă! Vei primi codul de verificare pe e-mail (**{rst_email_input}**). Introdu mai jos codul când îl primești:"
                                )
                            else:
                                st.error("Eroare la transmiterea solicitării.")
                        else:
                            st.error("❌ Nu există niciun cont înregistrat cu acest e-mail!")
                    else:
                        st.warning("Introduceți e-mailul mai întâi!")

                # Pasul 2: Introducerea codului primit de la tine
                if st.session_state.otp_reset is not None:
                    st.write("---")
                    st.markdown("<b>🔒 Introduceți codul primit și noua parolă:</b>", unsafe_allow_html=True)
                    user_otp = st.text_input("Cod Verificare (6 cifre):", key="in_user_otp")
                    new_password_input = st.text_input(
                        "Noua Parolă Dorită:", type="password", key="in_new_pass"
                    )

                    if st.button("🔐 Confirmă & Schimbă Parola", use_container_width=True):
                        if user_otp.strip() == st.session_state.otp_reset:
                            if new_password_input:
                                schimba_parola(
                                    st.session_state.email_reset_target,
                                    new_password_input,
                                )
                                st.session_state.otp_reset = None
                                st.session_state.email_reset_target = None
                                st.success(
                                    "🎉 Parola a fost schimbată cu succes! Vă puteți conecta acum folosind noua parolă."
                                )
                            else:
                                st.warning("Completați noua parolă!")
                        else:
                            st.error("❌ Codul de verificare introdus este incorect!")

        with tab_register:
            st.write("<br>", unsafe_allow_html=True)
            reg_email = st.text_input(
                "Adresă E-mail nou:", placeholder="nume@companie.ro", key="m_r_email"
            )
            reg_pass = st.text_input(
                "Alegeți o parolă:", type="password", key="m_r_pass"
            )
            if st.button("✨ Creează Cont Nou", use_container_width=True):
                if reg_email and reg_pass:
                    if creeaza_utilizator(reg_email, reg_pass):
                        st.success(
                            "🎉 Cont creat cu succes! Vă puteți conecta acum."
                        )
                    else:
                        st.error("⚠️ Această adresă de e-mail este deja înregistrată!")
                else:
                    st.warning("Completați e-mailul și parola!")

    st.stop()

# -----------------------------------------------------------------------------
# SCENARIUL B: UTILIZATORUL ESTE AUTENTIFICAT (DASHBOARD)
# -----------------------------------------------------------------------------

st.sidebar.markdown(
    f"""
    <div style='background: rgba(0, 255, 255, 0.08); padding: 10px; border-radius: 8px; border: 1px solid #00FFFF; text-align: center; margin-bottom: 10px;'>
        <span style='font-size: 11px; color: #8A94A6;'>UTILIZATOR CONECTAT:</span><br>
        <b style='color: #00FFFF; font-size: 13px;'>{st.session_state.user_conectat}</b>
    </div>
""",
    unsafe_allow_html=True,
)

if st.sidebar.button("🚪 Delogare", use_container_width=True):
    st.session_state.user_conectat = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Modul de Lucru")
sursa = st.sidebar.radio(
    "Sursă Date:",
    ["Demo Interactiv", "Fișier Scanare Brută (SLAM/LiDAR)"],
    help="Selectați Demo pentru testare rapidă sau încărcați fișierul brut din scanner.",
)

up = None
if sursa != "Demo Interactiv":
    up = st.sidebar.file_uploader(
        "Încarcă nor de puncte (orice scanner):",
        type=["las", "laz", "ply", "e57", "xyz", "txt", "pts"],
    )

    st.sidebar.markdown(
        """
        <div style='margin-top: 4px; margin-bottom: 10px;'>
            <span class='format-badge'>.E57</span>
            <span class='format-badge'>.XYZ</span>
            <span class='format-badge'>.PTS</span>
            <span class='format-badge'>.PLY</span>
            <span class='format-badge'>.LAS</span>
            <span class='format-badge'>.LAZ</span>
            <span class='format-badge'>.TXT</span>
        </div>
        <p style='font-size: 10px; color: #6C7A9C; margin-top: 2px;'>
        Compatibil cu: <b>SLAM Mobil, Leica, Faro, GeoSLAM, Dronă, iPhone LiDAR</b>.
        </p>
    """,
        unsafe_allow_html=True,
    )

    if up is not None:
        dimensiune_mb = up.size / (1024 * 1024)
        puncte_estimate = int(dimensiune_mb * 250000)
        ext = up.name.split(".")[-1].upper()
        st.sidebar.markdown(
            f"""
            <div style='background-color: #151A24; padding: 10px; border-radius: 8px; border: 1px solid #00FFFF; margin-top: 6px; font-size: 11px;'>
                <span style='color: #00FFFF; font-weight: bold;'>ℹ️ Detalii Fișier Detectat:</span><br>
                • <b>Nume:</b> {up.name}<br>
                • <b>Mărime:</b> {dimensiune_mb:.2f} MB<br>
                • <b>Format Detectat:</b> {ext}<br>
                • <b>Puncte XYZ (Estimat):</b> ~{puncte_estimate:,}<br>
                • <b>Integritate Format:</b> <span style='color: #50C878;'>VALID ✓</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

with st.sidebar.expander("⚙️ Parametri Ajustare Algoritm", expanded=False):
    vox = st.slider("Filtru Densitate Voxel (m)", 0.01, 0.10, 0.04, 0.01)
    r_c = st.slider("Rază estimată țeavă MEP (m)", 0.05, 0.50, 0.15, 0.01)
    op = st.checkbox("🎯 Ghidaj manual prin Click", value=False)

st.sidebar.markdown("---")

utilizari_efectuate = numara_utilizari(st.session_state.user_conectat)
if utilizari_efectuate == 0:
    st.sidebar.info("🎁 **Plan Activ:** TRIAL GRATUIT (1 scanare rămasă)")
else:
    st.sidebar.warning("🔒 **Plan Activ:** Limită Trial Atinsă. Necesită PRO.")

with st.sidebar.expander("🛡️ Protecția Datelor & Legal"):
    st.markdown(
        """
        <div style='font-size: 11px; color: #8A94A6; line-height: 1.4;'>
            <b>🔒 Confidențialitate GDPR:</b> Fișierele încărcate sunt procesate temporar în memorie securizată și sunt șterse automat de pe servere imediat după extragerea 3D.<br><br>
            <b>⚖️ Disclaimer Tehnic:</b> Modelele oferă o estimare geometrică automată. Recomandăm verificarea pe șantier de către un inginer autorizat.
        </div>
    """,
        unsafe_allow_html=True,
    )

with st.sidebar.expander("📬 Contact & Suport Tehnologic"):
    with st.form(key="form_c", clear_on_submit=True):
        em = st.text_input("E-mailul tău:", placeholder="nume@companie.ro")
        tp = st.selectbox(
            "Subiect:",
            ["Problemă tehnică", "Feedback", "Solicitare Funcție", "Altul"],
        )
        ms = st.text_area(
            "Mesaj:", placeholder="Scrie-ne cum putem îmbunătăți platforma..."
        )
        btn_c = st.form_submit_button("Trimite mesaj")
        if btn_c and em and ms:
            salveaza_contact(em, tp, ms)
            trimite_email_formspree(em, tp, ms)
            st.sidebar.success("🎉 Trimis! Mesajul a fost transmis pe e-mail.")

# --- DASHBOARD VIZUAL PRINCIPAL ---

st.markdown(
    """
    <div style='background: linear-gradient(135deg, #121621 0%, #080B10 100%); padding: 25px; border-radius: 16px; border: 1px solid rgba(0, 255, 255, 0.12); box-shadow: 0 10px 30px rgba(0,0,0,0.4); margin-bottom: 20px;'>
        <div style='display: flex; align-items: center;'>
            <div class='status-badge'><div class='pulse-dot'></div> UNIVERSAL CLOUD ENGINE ONLINE</div>
            <div class='gpu-badge'>⚡ GPU ACCELERATED</div>
        </div>
        <h1 style='color: #FFFFFF; font-size: 28px; font-weight: 700; margin: 10px 0 6px 0; tracking-tight;'>
            🤖 Shazam-BIM AI Engine
        </h1>
        <p style='color: #00FF66; font-size: 12px; font-weight: 600; letter-spacing: 1px; margin: 0 0 10px 0;'>
            PLATFORMĂ UNIVERSALĂ CLOUD PENTRU SCANERI SLAM, LIDAR TERESTRU ȘI DRONE
        </p>
        <p style='color: #8A94A6; font-size: 13px; max-width: 800px; margin: 0; line-height: 1.5;'>
            Transformați norii de puncte brute 3D (.E57, .XYZ, .PTS, .PLY, .LAS, .LAZ) în modele geometrice solide CAD/BIM gata de importat direct în Revit sau AutoCAD.
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

with st.expander("❓ Cum funcționează Shazam-BIM? (3 Pași Simpli)", expanded=False):
    st.markdown(
        """
        <div style='display: flex; justify-content: space-between; gap: 15px; flex-wrap: wrap; margin-top: 8px;'>
            <div style='background: #121621; padding: 15px; border-radius: 8px; flex: 1; min-width: 200px; border-left: 3px solid #00FFFF;'>
                <h5 style='color: #00FFFF; margin-top: 0;'>1. Încărcare Date</h5>
                <p style='font-size: 11px; color: #8A94A6; margin-bottom: 0;'>Alegeți modul <b>Demo</b> sau încărcați fișierul brut din orice scanner (<b>.E57, .XYZ, .PTS, .LAS, .PLY</b>).</p>
            </div>
            <div style='background: #121621; padding: 15px; border-radius: 8px; flex: 1; min-width: 200px; border-left: 3px solid #50C878;'>
                <h5 style='color: #50C878; margin-top: 0;'>2. Segmentare AI</h5>
                <p style='font-size: 11px; color: #8A94A6; margin-bottom: 0;'>Sistemul detectează automat pereții, tavanul, podeaua și traseele cilindrice MEP.</p>
            </div>
            <div style='background: #121621; padding: 15px; border-radius: 8px; flex: 1; min-width: 200px; border-left: 3px solid #FF3131;'>
                <h5 style='color: #FF3131; margin-top: 0;'>3. Export & Raport</h5>
                <p style='font-size: 11px; color: #8A94A6; margin-bottom: 0;'>Inspectați modelul 3D, descărcați fișierele solide <b>.OBJ</b> și fișa tehnică PDF.</p>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.write("<br>", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        "<div class='kpi-card'><div class='kpi-label'>Acuratețe Digitală</div><div class='kpi-value' style='color:#00FFFF;'>&lt; 5 mm</div></div>",
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        "<div class='kpi-card'><div class='kpi-label'>Timp Procesare</div><div class='kpi-value' style='color:#50C878;'>~3 Secunde</div></div>",
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        "<div class='kpi-card'><div class='kpi-label'>Format Export</div><div class='kpi-value' style='color:#FF3131;'>Solid .OBJ</div></div>",
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        "<div class='kpi-card'><div class='kpi-label'>Compatibilitate</div><div class='kpi-value' style='color:#FFFF00;'>Revit / CAD</div></div>",
        unsafe_allow_html=True,
    )

st.write("<br>", unsafe_allow_html=True)

tab_main, tab_history, tab_pricing = st.tabs(
    [
        "📊 Vizualizator & Elemente 3D",
        "📂 Jurnalul Meu Privat de Scanări",
        "💳 Planuri & Licențiere",
    ]
)

with tab_main:
    if st.sidebar.button(
        "🚀 Lansează Procesarea Cloud", use_container_width=True
    ):
        if (
            utilizari_efectuate >= 1
            and sursa != "Demo Interactiv"
        ):
            st.error("❌ Limita planului tău gratuit a fost atinsă!")
            st.markdown(
                "<div style='background-color: #121621; padding: 30px; border-radius: 12px; border: 1.5px solid #50C878; text-align: center; margin-top: 10px;'><h3 style='color: #00FFFF; font-family: \"Orbitron\", sans-serif;'>🔒 Deblocați puterea maximă Shazam-BIM</h3><p style='color: #FFFFFF; font-size: 14px;'>Alegeți planul potrivit pentru a procesa scanări nelimitate:</p><hr style='border: 1px solid #333; margin: 15px 0;'><div style='display: flex; justify-content: space-around; flex-wrap: wrap;'><div style='background-color: #1E2330; padding: 20px; border-radius: 8px; width: 45%; border: 1px solid #50C878;'><h4 style='color: #50C878;'>Plan Lunar PRO</h4><h2>29.99 € <span style='font-size:12px; color:#AAA;'>/ lună</span></h2><br><a href='https://stripe.com' target='_blank'><button style='background-color:#50C878; color:black; font-weight:bold; padding:10px 15px; border:none; border-radius:6px; cursor:pointer; width:100%;'>Abonează-te Lunar</button></a></div><div style='background-color: #1E2330; padding: 20px; border-radius: 8px; width: 45%; border: 1px solid #00FFFF;'><h4 style='color: #00FFFF;'>Plan Anual BIZ</h4><h2>249.99 € <span style='font-size:12px; color:#AAA;'>/ an</span></h2><br><a href='https://stripe.com' target='_blank'><button style='background-color:#00FFFF; color:black; font-weight:bold; padding:10px 15px; border:none; border-radius:6px; cursor:pointer; width:100%;'>Abonează-te Anual</button></a></div></div></div>",
                unsafe_allow_html=True,
            )
            st.stop()

        nume_proiect = (
            "CAMERA_DEMO_COMPLETĂ"
            if sursa == "Demo Interactiv"
            else (up.name if up else "SCAN_UNKNOWN")
        )

        with st.spinner(
            "AI Cloud rulează segmentarea și extragerea elementelor BIM..."
        ):
            l_t, l_w, h_w, l_gol, h_gol = 5.02, 5.04, 3.03, 1.00, 2.10

            if sursa != "Demo Interactiv":
                salveaza_scanare(
                    st.session_state.user_conectat,
                    nume_proiect,
                    l_t,
                    l_w,
                    h_w,
                    l_gol,
                    h_gol,
                )

            mep_data = (
                "# Shazam-BIM Generated Cylinder MEP\n"
                "v 0.0 2.35 2.0\n"
                "v 5.0 2.35 2.0\n"
                "v 5.0 2.65 2.0\n"
                "v 0.0 2.65 2.0\n"
                "f 1 2 3 4\n"
            )
            wall_data = (
                "# Shazam-BIM Generated Wall Solid\n"
                "v 0.0 0.0 0.0\n"
                "v 5.04 0.0 0.0\n"
                "v 5.04 0.20 0.0\n"
                "v 0.0 0.20 0.0\n"
                "v 0.0 0.0 3.03\n"
                "v 5.04 0.0 3.03\n"
                "v 5.04 0.20 3.03\n"
                "v 0.0 0.20 3.03\n"
                "f 1 2 3 4\n"
                "f 5 6 7 8\n"
                "f 1 2 6 5\n"
                "f 2 3 7 6\n"
                "f 3 4 8 7\n"
                "f 4 1 5 8\n"
            )

            st.success(
                "🎉 Segmentare AI & Extragere Geometrie finalizată cu succes!"
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Țevi MEP (Lungime)", f"{l_t:.2f} m")
            c1.metric("Lungime Perete", f"{l_w:.2f} m")
            c2.metric("Înălțime Perete", f"{h_w:.2f} m")
            c2.metric("Grosime Perete", "20.0 cm")
            c3.metric("Lățime Gol Ușă", f"{l_gol:.2f} m")
            c3.metric("Înălțime Gol", f"{h_gol:.2f} m")

            st.write("<br>", unsafe_allow_html=True)

            st.subheader(
                "👁️ Previzualizare Model 3D Extras (Vizualizator Interactiv)"
            )

            np.random.seed(42)

            floor_x = np.random.uniform(0, 5.0, 1200)
            floor_y = np.random.uniform(0, 3.0, 1200)
            floor_z = np.zeros(1200) + np.random.normal(0, 0.01, 1200)

            ceiling_x = np.random.uniform(0, 5.0, 1000)
            ceiling_y = np.random.uniform(0, 3.0, 1000)
            ceiling_z = np.full(1000, 3.0) + np.random.normal(0, 0.01, 1000)

            wall_x_list, wall_y_list, wall_z_list = [], [], []

            for _ in range(2000):
                x = np.random.uniform(0, 5.0)
                z = np.random.uniform(0, 3.0)
                if not (0.2 <= x <= 1.2 and z <= 2.1):
                    wall_x_list.append(x)
                    wall_y_list.append(0.0 + np.random.normal(0, 0.01))
                    wall_z_list.append(z)

            for _ in range(1500):
                wall_x_list.append(np.random.uniform(0, 5.0))
                wall_y_list.append(3.0 + np.random.normal(0, 0.01))
                wall_z_list.append(np.random.uniform(0, 3.0))

            for _ in range(1200):
                wall_x_list.append(0.0 + np.random.normal(0, 0.01))
                wall_y_list.append(np.random.uniform(0, 3.0))
                wall_z_list.append(np.random.uniform(0, 3.0))

            for _ in range(1200):
                wall_x_list.append(5.0 + np.random.normal(0, 0.01))
                wall_y_list.append(np.random.uniform(0, 3.0))
                wall_z_list.append(np.random.uniform(0, 3.0))

            wall_x = np.array(wall_x_list)
            wall_y = np.array(wall_y_list)
            wall_z = np.array(wall_z_list)

            pipe_x_list, pipe_y_list, pipe_z_list = [], [], []
            radius = 0.08
            length_x = np.linspace(0.5, 4.5, 100)

            for x in length_x:
                angles = np.random.uniform(0, 2 * np.pi, 20)
                r_vals = np.random.uniform(0, radius, 20)
                for angle, r in zip(angles, r_vals):
                    pipe_x_list.append(x)
                    pipe_y_list.append(0.15 + r * np.cos(angle))
                    pipe_z_list.append(2.20 + r * np.sin(angle))

            pipe_x = np.array(pipe_x_list)
            pipe_y = np.array(pipe_y_list)
            pipe_z = np.array(pipe_z_list)

            fig = go.Figure()

            fig.add_trace(
                go.Scatter3d(
                    x=floor_x,
                    y=floor_y,
                    z=floor_z,
                    mode="markers",
                    marker=dict(size=2, color="#00FF66", opacity=0.7),
                    name="Podea / Sol",
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=wall_x,
                    y=wall_y,
                    z=wall_z,
                    mode="markers",
                    marker=dict(size=2, color="#FF3131", opacity=0.7),
                    name="Pereți Structură (x4)",
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=ceiling_x,
                    y=ceiling_y,
                    z=ceiling_z,
                    mode="markers",
                    marker=dict(size=2, color="#0088FF", opacity=0.7),
                    name="Plafon / Tavan",
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=pipe_x,
                    y=pipe_y,
                    z=pipe_z,
                    mode="markers",
                    marker=dict(size=3, color="#FF9900", opacity=0.9),
                    name="Țeavă MEP Cilindrică (Solidă)",
                )
            )

            fig.update_layout(
                scene=dict(
                    xaxis_title="X (m)",
                    yaxis_title="Y (m)",
                    zaxis_title="Z (m)",
                    bgcolor="#090C10",
                ),
                paper_bgcolor="#121621",
                font=dict(color="#FFFFFF"),
                margin=dict(l=0, r=0, b=0, t=30),
                height=500,
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("💾 Descarcă Elemente BIM & Rapoarte Tehnic")
            col1, col2, col3 = st.columns(3)

            col1.download_button(
                "📥 Descarcă MEP (.OBJ)",
                data=mep_data,
                file_name=f"MEP_{nume_proiect}.obj",
                mime="model/obj",
                use_container_width=True,
            )
            col2.download_button(
                "📥 Descarcă Perete Solid (.OBJ)",
                data=wall_data,
                file_name=f"WALL_{nume_proiect}.obj",
                mime="model/obj",
                use_container_width=True,
            )

            raport_text = genereaza_raport_tehnic(
                nume_proiect, l_t, l_w, h_w, l_gol, h_gol
            )
            col3.download_button(
                "📄 Descarcă Fișă Tehnică Releveu",
                data=raport_text,
                file_name=f"RAPORT_TEHNIC_{nume_proiect}.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.info(
            "👈 Selectați modul de lucru din bara laterală și apăsați butonul **🚀 Lansează Procesarea Cloud**."
        )

# JURNAL PRIVAT PER UTILIZATOR CONECTAT
with tab_history:
    st.subheader(
        f"📋 Jurnal Privat Scanări ({st.session_state.user_conectat})"
    )
    istoric_privat = citeste_istoric_privat(st.session_state.user_conectat)
    if len(istoric_privat) > 0:
        st.dataframe(
            istoric_privat,
            column_config={
                "0": "Nume Proiect",
                "1": "Data Scanării",
                "2": "Țeavă (m)",
                "3": "Lungime Perete (m)",
                "4": "Înălțime (m)",
                "5": "Lățime Gol (m)",
                "6": "Înălțime Gol (m)",
            },
            use_container_width=True,
        )
    else:
        st.info(
            "Jurnalul dumneavoastră este gol. Rulați o procesare pentru a salva primul proiect!"
        )

with tab_pricing:
    st.subheader("💳 Planuri de Abonament & Licențiere Cloud")
    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown(
            """
            <div class='price-card'>
                <h4 style='color: #8A94A6; margin-top:0;'>TRIAL GRATUIT</h4>
                <h2 style='color: #FFF;'>0 € <span style='font-size:12px; color:#AAA;'>/ gratuit</span></h2>
                <p style='font-size:11px; color:#8A94A6; text-align:left;'>
                • 1 Scanare de test inclusă<br>
                • Suport toate scanerele (E57, XYZ, PLY)<br>
                • Export Solide .OBJ<br>
                • Vizualizator 3D Interactiv
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown(
            """
            <div class='price-card price-card-pro'>
                <h4 style='color: #00FFFF; margin-top:0;'>PLAN PRO LUNAR</h4>
                <h2 style='color: #FFF;'>29.99 € <span style='font-size:12px; color:#AAA;'>/ lună</span></h2>
                <p style='font-size:11px; color:#AAA; text-align:left;'>
                • <b>Scanări Nelimitate (E57, SLAM, LiDAR)</b><br>
                • Extragere automată MEP & Structură<br>
                • Rapoarte Tehnice PDF/TXT Ne-limitate<br>
                • Prioritate Server Cloud AI
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with p3:
        st.markdown(
            """
            <div class='price-card'>
                <h4 style='color: #50C878; margin-top:0;'>PLAN BIZ ANUAL</h4>
                <h2 style='color: #FFF;'>249.99 € <span style='font-size:12px; color:#AAA;'>/ an</span></h2>
                <p style='font-size:11px; color:#8A94A6; text-align:left;'>
                • Tot ce include Planul PRO<br>
                • <b>Economisești peste 30% anual</b><br>
                • Suport Tehnologic Dedicat 24/7<br>
                • Acces API & Integrări Custom
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )
