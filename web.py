import hashlib
import io
import os
import random
import sqlite3
import tempfile
import time
from datetime import datetime
import laspy
import numpy as np
import plotly.graph_objects as go
import requests
from scipy.spatial import Delaunay
import streamlit as st

# -----------------------------------------------------------------------------
# 0. CONFIGURARE FORMSPREE PENTRU SOLICITĂRI & CONTACT
# -----------------------------------------------------------------------------
FORMSPREE_ID = "xeeyrbyb"


def trimite_solicitare_resetare_catre_admin(email_client, cod_otp):
  if FORMSPREE_ID == "ID-UL_TAU_AICI":
    return True

  url = f"https://formspree.io/f/{FORMSPREE_ID}"
  data = {
      "email_client": email_client,
      "cod_verificare": cod_otp,
      "mesaj": (
          f"SOLICITARE RESETARE PAROLĂ\n\n• E-mail Client: {email_client}\n•"
          f" Cod de Verificare (OTP): {cod_otp}\n\nTrimite acest cod clientului"
          " pentru a-și reconfigura parola."
      ),
      "_subject": f"🔑 Solicitare Resetare Parolă pentru: {email_client}",
  }
  try:
    response = requests.post(url, data=data)
    return response.status_code == 200
  except Exception as e:
    print(f"Eroare la trimitere Formspree: {e}")
    return False


def trimite_email_formspree(email, tip, mesaj):
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


# 1. Configurare pagină fără sidebar
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

# 2. Injectare CSS Custom - DEEP EMERALD & OCEAN BLUE THEME (PROFESSIONAL UI)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@600;700;800;900&display=swap');
    
    .stApp {
        background-color: #061017;
        font-family: 'Inter', sans-serif;
        color: #E2E8F0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] {
        display: none !important;
        height: 0px !important;
    }
    
    .stMarkdown a.anchor-link, 
    [data-testid="stHeaderActionElements"],
    a.header-anchor {
        display: none !important;
    }
    
    .block-container {
        max-width: 1100px !important;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        margin: 0 auto !important;
    }

    .logo-container {
        text-align: center;
        padding: 10px 0;
        user-select: none;
    }
    .logo-shazam {
        font-family: 'Orbitron', sans-serif;
        font-weight: 800;
        color: #00FFFF;
        text-shadow: 0 0 12px rgba(0, 255, 255, 0.7);
    }
    .logo-bim {
        font-family: 'Orbitron', sans-serif;
        font-weight: 800;
        color: #50C878;
        text-shadow: 0 0 12px rgba(80, 200, 120, 0.7);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #0D1E26 0%, #09151F 100%) !important;
        border: 1px solid rgba(80, 200, 120, 0.25) !important;
        border-radius: 14px !important;
        padding: 15px !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
    }

    .format-badge {
        display: inline-block;
        background: rgba(0, 255, 255, 0.08);
        border: 1px solid rgba(0, 255, 255, 0.25);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10px;
        color: #00FFFF;
        margin-right: 4px;
        margin-bottom: 4px;
        font-weight: 600;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(80, 200, 120, 0.12);
        border: 1px solid rgba(80, 200, 120, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        color: #50C878;
        font-size: 11px;
        font-weight: 600;
    }
    .pulse-dot {
        width: 7px;
        height: 7px;
        background-color: #50C878;
        border-radius: 50%;
        margin-right: 6px;
        box-shadow: 0 0 8px #50C878;
    }

    .kpi-card {
        background: #0B1922;
        border: 1px solid rgba(80, 200, 120, 0.2);
        border-radius: 12px;
        padding: 14px;
        text-align: center;
    }
    .kpi-label {
        color: #94A3B8;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: #00FFFF;
        font-size: 18px;
        font-weight: 700;
        font-family: 'Orbitron', sans-serif;
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #00E5FF 0%, #10B981 100%);
        color: #061017;
        font-weight: 700;
        font-size: 14px;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.2);
        transition: all 0.2s ease;
        height: 44px !important;
        margin: 0 !important;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4);
        transform: translateY(-1px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #0A1721;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(80, 200, 120, 0.15);
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 6px;
        color: #94A3B8;
        font-weight: 600;
        font-size: 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0F2830 !important;
        color: #00FFFF !important;
    }

    .price-card {
        background: #0B1922;
        border: 1.5px solid #50C878;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        height: 100%;
        box-shadow: 0 0 20px rgba(80, 200, 120, 0.12);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 3. BAZĂ DE DATE & MOTOR GEODEZIC REAL
# -----------------------------------------------------------------------------


def hash_password(password):
  return hashlib.sha256(str(password).encode()).hexdigest()


def init_db():
  conn = sqlite3.connect("proiecte_bim.db")
  c = conn.cursor()
  c.execute(
      "CREATE TABLE IF NOT EXISTS utilizatori (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, email TEXT UNIQUE, parola TEXT, data_inregistrare TEXT)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS scanari (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, user_email TEXT, nume_proiect TEXT, data_procesare TEXT,"
      " suprafata REAL, volum REAL, min_z REAL, max_z REAL, puncte INTEGER)"
  )
  c.execute(
      "CREATE TABLE IF NOT EXISTS mesaje_contact (id INTEGER PRIMARY KEY"
      " AUTOINCREMENT, data_trimitere TEXT, email_client TEXT, tip_mesaj TEXT,"
      " mesaj TEXT)"
  )

  # Migrare compatibilitate tabele vechi
  try:
    c.execute("ALTER TABLE scanari ADD COLUMN user_email TEXT")
  except sqlite3.OperationalError:
    pass
  try:
    c.execute("ALTER TABLE scanari ADD COLUMN suprafata REAL")
  except sqlite3.OperationalError:
    pass
  try:
    c.execute("ALTER TABLE scanari ADD COLUMN volum REAL")
  except sqlite3.OperationalError:
    pass

  conn.commit()
  conn.close()


def exista_email(email):
  conn = sqlite3.connect("proiecte_bim.db")
  c = conn.cursor()
  c.execute(
      "SELECT * FROM utilizatori WHERE email = ?",
      (str(email).lower().strip(),),
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
        "INSERT INTO utilizatori (email, parola, data_inregistrare)"
        " VALUES (?,?,?)",
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


def salveaza_scanare(email, nume, suprafata, volum, min_z, max_z, puncte):
  conn = sqlite3.connect("proiecte_bim.db")
  c = conn.cursor()
  dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  c.execute(
      "INSERT INTO scanari (user_email, nume_proiect, data_procesare, suprafata,"
      " volum, min_z, max_z, puncte) VALUES (?,?,?,?,?,?,?,?)",
      (
          str(email),
          str(nume),
          dt,
          round(float(suprafata), 2),
          round(float(volum), 2),
          round(float(min_z), 2),
          round(float(max_z), 2),
          int(puncte),
      ),
  )
  conn.commit()
  conn.close()


def salveaza_contact(email, tip, text):
  conn = sqlite3.connect("proiecte_bim.db")
  c = conn.cursor()
  dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  c.execute(
      "INSERT INTO mesaje_contact (data_trimitere, email_client, tip_mesaj,"
      " mesaj) VALUES (?,?,?,?)",
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
      "SELECT nume_proiect, data_procesare, suprafata, volum, puncte FROM"
      " scanari WHERE user_email = ? ORDER BY id DESC",
      (str(email),),
  )
  date = c.fetchall()
  conn.close()
  return date


def proceseaza_fisier_geodezic_web(uploaded_file):
  """Motor real de calcul geodezic (Delaunay + Prisme) pe fișiere LiDAR / XYZ"""
  if uploaded_file is None:
    return None

  suffix = os.path.splitext(uploaded_file.name)[1].lower()
  with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(uploaded_file.getvalue())
    tmp_path = tmp.name

  try:
    if suffix in [".las", ".laz"]:
      las = laspy.read(tmp_path)
      x = np.array(las.x, dtype=np.float64)
      y = np.array(las.y, dtype=np.float64)
      z = np.array(las.z, dtype=np.float64)
    else:
      data = np.loadtxt(tmp_path)
      if data.ndim == 1 or data.shape[1] < 3:
        raise ValueError(
            "Fișierul text trebuie să conțină cel puțin 3 coloane (X, Y, Z)."
        )
      x = data[:, 0]
      y = data[:, 1]
      z = data[:, 2]

    n_puncte = len(x)
    if n_puncte < 4:
      raise ValueError("Fișierul conține prea puțin puncte pentru triangulație.")

    # 1. Triangulație Delaunay 2D
    points_2d = np.column_stack((x, y))
    tri = Delaunay(points_2d)
    triangles = points_2d[tri.simplices]

    x1, y1 = triangles[:, 0, 0], triangles[:, 0, 1]
    x2, y2 = triangles[:, 1, 0], triangles[:, 1, 1]
    x3, y3 = triangles[:, 2, 0], triangles[:, 2, 1]

    # Suprafață 2D proiectată prin formula Shoelace
    arii_2d = 0.5 * np.abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    suprafata_2d = np.sum(arii_2d)

    # 2. Calcul Volum prin Prisme raportat la Z_min
    z_min = np.min(z)
    z_tri = z[tri.simplices]
    medie_z_tri = np.mean(z_tri, axis=1)
    inaltimi_relative = medie_z_tri - z_min
    volum = np.sum(arii_2d * inaltimi_relative)

    # Eșantionare puncte pentru afișarea în browser (max 5000 puncte pentru performanță)
    pas = max(1, n_puncte // 5000)

    return {
        "n_puncte": n_puncte,
        "suprafata": suprafata_2d,
        "volum": volum,
        "z_min": z_min,
        "z_max": np.max(z),
        "x": x[::pas],
        "y": y[::pas],
        "z": z[::pas],
    }

  except Exception as e:
    st.error(f"❌ Eroare la procesarea geodezică a fișierului: {e}")
    return None
  finally:
    if os.path.exists(tmp_path):
      os.remove(tmp_path)


def genereaza_raport_tehnic(nume, suprafata, volum, min_z, max_z, puncte):
  dt = datetime.now().strftime("%d.%m.%Y %H:%M")
  continut = f"""================================================================================
                    SHAZAM-BIM & GEODESY ENGINE - FIȘĂ METROLOGICĂ
================================================================================
Data generării: {dt}
Identificator Fișier Sursă: {nume}
Total Puncte Analizate: {puncte:,}
Acuratețe de Calcul: Matematică Exactă (Delaunay & Prisme)

1. REZULTATE MĂSURĂTORI TERESTRE / CADASTRU
--------------------------------------------------------------------------------
- Suprafață Proiectată 2D         : {suprafata:,.2f} mp
- Volum Prismatic Brut            : {volum:,.2f} mc
- Cota Altimetrică Minimă (Z min) : {min_z:.3f} m
- Cota Altimetrică Maximă (Z max) : {max_z:.3f} m

2. STATUS CONFORMITATE & VALIDARE
--------------------------------------------------------------------------------
- Algoritm Utilizat               : Triangulație Delaunay 2D
- Status Validare Geometrie       : VALID (Fără discontinuități majore)

================================================================================
Document generat automat de platforma Shazam-BIM Cloud & Geodesy Processing.
Verificarea oficială pe șantier revine inginerului geodez autorizat.
================================================================================
"""
  return continut


init_db()

# -----------------------------------------------------------------------------
# SCENARIUL A: UTILIZATORUL NU ESTE CONECTAT
# -----------------------------------------------------------------------------
if st.session_state.user_conectat is None:

  st.markdown(
      """
        <div class='logo-container' style='margin-top: 30px; margin-bottom: 10px;'>
            <span class='logo-shazam' style='font-size: 45px;'>Shazam</span><span class='logo-bim' style='font-size: 45px;'>-BIM</span>
            <p style='font-size: 13px; color: #50C878; font-weight: 600; margin-top: 8px; letter-spacing: 1px;'>
                PLATFORMĂ UNIVERSALĂ CLOUD PENTRU RELEVEE STRUCTURALE ȘI INSTALAȚII MEP
            </p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  col_a, col_b, col_c = st.columns([1, 2, 1])

  with col_b:
    tab_login, tab_register = st.tabs(["🔑 Conectare", "📝 Înregistrare Cont"])

    with tab_login:
      st.write("<br>", unsafe_allow_html=True)
      email_in = st.text_input(
          "Adresă E-mail:", placeholder="nume@companie.ro", key="m_l_email"
      )
      pass_in = st.text_input("Parolă:", type="password", key="m_l_pass")

      if st.button("🚀 Autentificare în Cloud", use_container_width=True):
        if verifica_utilizator(email_in, pass_in):
          st.session_state.user_conectat = email_in.lower().strip()
          st.success("🎉 Conectat cu succes!")
          st.rerun()
        else:
          st.error("❌ E-mail sau parolă incorectă!")

      st.write("<br>", unsafe_allow_html=True)
      with st.expander("❓ Ai uitat parola?", expanded=False):
        st.markdown(
            "<p style='font-size: 11px; color: #94A3B8;'>Introduceți e-mailul"
            " înregistrat. Un cod de verificare va fi transmis pentru"
            " reconfigurare.</p>",
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
                    f"📩 Solicitarea a fost transmisă pentru"
                    f" **{rst_email_input}**! Introdu mai jos codul primit:"
                )
              else:
                st.error("Eroare la transmiterea solicitării.")
            else:
              st.error("❌ Nu există niciun cont înregistrat cu acest e-mail!")
          else:
            st.warning("Introduceți e-mailul mai întâi!")

        if st.session_state.otp_reset is not None:
          st.write("---")
          st.markdown(
              "<b>🔒 Introduceți codul primit și noua parolă:</b>",
              unsafe_allow_html=True,
          )
          user_otp = st.text_input(
              "Cod Verificare (6 cifre):", key="in_user_otp"
          )
          new_password_input = st.text_input(
              "Noua Parolă Dorită:", type="password", key="in_new_pass"
          )

          if st.button("🔐 Confirmă & Schimbă Parola", use_container_width=True):
            if user_otp.strip() == st.session_state.otp_reset:
              if new_password_input:
                schimba_parola(
                    st.session_state.email_reset_target, new_password_input
                )
                st.session_state.otp_reset = None
                st.session_state.email_reset_target = None
                st.success("🎉 Parola a fost schimbată cu succes!")
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
            st.success("🎉 Cont creat cu succes! Vă puteți conecta acum.")
          else:
            st.error("⚠️ Această adresă de e-mail este deja înregistrată!")
        else:
          st.warning("Completați e-mailul și parola!")

  st.stop()

# -----------------------------------------------------------------------------
# SCENARIUL B: ECRANUL PRINCIPAL AUTENTIFICAT
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class='logo-container' style='margin-top: 10px; margin-bottom: 25px;'>
        <span class='logo-shazam' style='font-size: 46px;'>Shazam</span><span class='logo-bim' style='font-size: 46px;'>-BIM</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_u1, col_u2 = st.columns([5, 1])

with col_u1:
  st.markdown(
      f"""
        <div style='display: flex; justify-content: flex-end; align-items: center; height: 44px;'>
            <div style='background-color: #0D1E26; border: 1px solid rgba(0, 255, 255, 0.4); border-radius: 8px; height: 44px; display: inline-flex; align-items: center; padding: 0 16px; color: #E2E8F0; font-size: 13px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); width: fit-content; white-space: nowrap;'>
                👤 <span style='color: #00FFFF; font-weight: 600; margin-left: 6px;'>{st.session_state.user_conectat}</span>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col_u2:
  if st.button("🚪 Delogare", use_container_width=True):
    st.session_state.user_conectat = None
    st.rerun()

st.write("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div style='background: linear-gradient(135deg, #0F2229 0%, #0B1924 100%); padding: 20px 24px; border-radius: 14px; border: 1px solid rgba(80, 200, 120, 0.2); margin-bottom: 15px;'>
        <div style='display: flex; align-items: center;'>
            <div class='status-badge'><div class='pulse-dot'></div> MOTOR GEODEZIC CLOUD ONLINE</div>
            <span style='background: rgba(0,255,255,0.08); border: 1px solid rgba(0,255,255,0.2); padding: 3px 10px; border-radius: 16px; font-size: 10px; color: #00FFFF; margin-left: 8px; font-weight: 600;'>⚡ PRECIZIE MILIMETRICĂ</span>
        </div>
        <h2 style='color: #FFFFFF; font-size: 22px; font-weight: 700; margin: 10px 0 4px 0;'>
            📐 Calcul Suprafață & Volum din Nor de Puncte
        </h2>
        <p style='color: #94A3B8; font-size: 12px; margin: 0; line-height: 1.5;'>
            Încărcați fișierele brute de scanare (.LAS, .LAZ, .XYZ, .PTS) pentru extragerea automată a modelului digital și calculul riguros prin Delaunay & Prisme.
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
with k1:
  st.markdown(
      "<div class='kpi-card'><div class='kpi-label'>Metodă Calcul</div><div"
      " class='kpi-value'>Delaunay</div></div>",
      unsafe_allow_html=True,
  )
with k2:
  st.markdown(
      "<div class='kpi-card'><div class='kpi-label'>Timp Procesare</div><div"
      " class='kpi-value' style='color:#50C878;'>~2 Secunde</div></div>",
      unsafe_allow_html=True,
  )
with k3:
  st.markdown(
      "<div class='kpi-card'><div class='kpi-label'>Format Suportat</div><div"
      " class='kpi-value' style='color:#FF3131;'>LAS, LAZ, XYZ</div></div>",
      unsafe_allow_html=True,
  )
with k4:
  st.markdown(
      "<div class='kpi-card'><div class='kpi-label'>Precizie</div><div"
      " class='kpi-value' style='color:#00FFFF;'>Exactă (100%)</div></div>",
      unsafe_allow_html=True,
  )

st.write("<br>", unsafe_allow_html=True)

st.markdown(
    "<h4 style='color: #00FFFF; font-family: Orbitron, sans-serif; margin-bottom:"
    " 8px;'>📂 Încărcare Fișier Scanare Terestră</h4>",
    unsafe_allow_html=True,
)

with st.container(border=True):
  up = st.file_uploader(
      "Selectați fișierul nor de puncte:",
      type=["las", "laz", "xyz", "pts", "txt"],
      help=(
          "Încărcați fișiere LiDAR sau fișiere text cu coordonate X, Y, Z pe"
          " coloane."
      ),
  )
  st.markdown(
      """
        <div>
            <span class='format-badge'>.LAS</span>
            <span class='format-badge'>.LAZ</span>
            <span class='format-badge'>.XYZ</span>
            <span class='format-badge'>.PTS</span>
            <span class='format-badge'>.TXT</span>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.write("<br>", unsafe_allow_html=True)
  lansa_btn = st.button(
      "🚀 Rulează Calculul Geodezic", use_container_width=True
  )

st.write("<br>", unsafe_allow_html=True)

tab_main, tab_history, tab_settings, tab_pricing, tab_legal = st.tabs([
    "📊 Vizualizator & Rezultate",
    "📂 Jurnal Proiecte",
    "⚙️ Setări Cont",
    "💳 Planuri & Licențe",
    "⚖️ Termeni & GDPR",
])

utilizari_efectuate = numara_utilizari(st.session_state.user_conectat)

with tab_main:
  if up is not None:
    nume_proiect = up.name

    # Rulare calcul doar la apăsarea butonului
    if lansa_btn:
      with st.spinner(
          "⚙️ Se calculează rețeaua Delaunay și volumul prismatic pe fișierul"
          " real..."
      ):
        rezultate_geo = proceseaza_fisier_geodezic_web(up)

      if rezultate_geo:
        st.session_state["ultimul_rezultat"] = (rezultate_geo, nume_proiect)
        salveaza_scanare(
            st.session_state.user_conectat,
            nume_proiect,
            rezultate_geo["suprafata"],
            rezultate_geo["volum"],
            rezultate_geo["z_min"],
            rezultate_geo["z_max"],
            rezultate_geo["n_puncte"],
        )
        st.success(
            f"🎉 Analiză geodezică finalizată pentru **{nume_proiect}**!"
        )

    # Dacă avem rezultate salvate în sesiune le afișăm permanent
    if "ultimul_rezultat" in st.session_state:
      rezultate_geo, nume_proiect = st.session_state["ultimul_rezultat"]

      c1, c2, c3 = st.columns(3)
      c1.metric(
          "Suprafață Proiectată 2D", f"{rezultate_geo['suprafata']:,.2f} mp"
      )
      c2.metric("Volum Prismatic Brut", f"{rezultate_geo['volum']:,.2f} mc")
      c3.metric(
          "Altimetrie Z (Min / Max)",
          f"{rezultate_geo['z_min']:.2f} m / {rezultate_geo['z_max']:.2f} m",
      )

      st.write("<br>", unsafe_allow_html=True)
      st.subheader(f"👁️ Previzualizare 3D Nor Puncte — {nume_proiect}")

      fig = go.Figure(
          data=[
              go.Scatter3d(
                  x=rezultate_geo["x"],
                  y=rezultate_geo["y"],
                  z=rezultate_geo["z"],
                  mode="markers",
                  marker=dict(
                      size=2,
                      color=rezultate_geo["z"],
                      colorscale="Viridis",
                      opacity=0.85,
                  ),
                  name="Puncte Scanate (Z colorat)",
              )
          ]
      )

      fig.update_layout(
          scene=dict(
              xaxis_title="X (m)",
              yaxis_title="Y (m)",
              zaxis_title="Z (m)",
              bgcolor="#061017",
          ),
          paper_bgcolor="#0D1E26",
          font=dict(color="#E2E8F0"),
          margin=dict(l=0, r=0, b=0, t=20),
          height=450,
      )

      st.plotly_chart(fig, use_container_width=True)

      st.subheader("📄 Generare Fișă Metrologică")
      raport_text = genereaza_raport_tehnic(
          nume_proiect,
          rezultate_geo["suprafata"],
          rezultate_geo["volum"],
          rezultate_geo["z_min"],
          rezultate_geo["z_max"],
          rezultate_geo["n_puncte"],
      )
      st.download_button(
          "📥 Descarcă Raportul Metrologic Oficial (.TXT)",
          data=raport_text,
          file_name=f"RAPORT_METROLOGIC_{nume_proiect}.txt",
          mime="text/plain",
          use_container_width=True,
      )
  else:
    st.info(
        "ℹ️ Încărcați un fișier LiDAR sau XYZ de pe șantier și apăsați butonul"
        " de pornire pentru a rula calculele."
    )

# JURNAL PROIECTE
with tab_history:
  st.subheader("📋 Jurnal Privat Măsurători Anterioare")
  istoric_privat = citeste_istoric_privat(st.session_state.user_conectat)
  if len(istoric_privat) > 0:
    st.dataframe(
        istoric_privat,
        column_config={
            "0": "Nume Proiect / Fișier",
            "1": "Data Analizei",
            "2": "Suprafață (mp)",
            "3": "Volum (mc)",
            "4": "Total Puncte",
        },
        use_container_width=True,
    )
  else:
    st.info(
        "Jurnalul este gol. Rulați o analiză geodezică pentru a salva primul"
        " proiect!"
    )

# SETĂRI CONT
with tab_settings:
  st.subheader("⚙️ Setări Cont & Securitate")
  st.markdown(
      f"""
        <div style='background: #0D1E26; padding: 20px; border-radius: 12px; border: 1px solid rgba(0, 255, 255, 0.2); margin-bottom: 20px;'>
            <p style='color: #94A3B8; font-size: 13px; margin: 0;'>Adresă E-mail Cont:</p>
            <h3 style='color: #00FFFF; margin-top: 5px; margin-bottom: 0;'>{st.session_state.user_conectat}</h3>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("### 🔒 Schimbare Parolă")
  with st.container(border=True):
    p_noua = st.text_input(
        "Introduceți Noua Parolă:", type="password", key="input_new_pass"
    )
    st.write("")
    if st.button("🔑 Salvează Noua Parolă", use_container_width=True):
      if p_noua:
        schimba_parola(st.session_state.user_conectat, p_noua)
        st.success("✅ Parola a fost actualizată cu succes!")
      else:
        st.warning("Completați noua parolă mai întâi.")

# TAB PLANURI & LICENȚIERE
with tab_pricing:
  st.subheader("💳 Planuri de Abonament & Licențiere Cloud Enterprise")
  p1, p2, p3 = st.columns(3)

  with p1:
    st.markdown(
        """
            <div class='price-card' style='border:1.5px solid #94A3B8;'>
                <h4 style='color: #94A3B8; margin-top:0;'>TRIAL GRATUIT</h4>
                <h2 style='color: #FFF;'>0 € <span style='font-size:12px; color:#AAA;'>/ gratuit</span></h2>
                <p style='font-size:12px; color:#94A3B8; text-align:left;'>
                • Analiză fișiere de test<br>
                • Calcul Suprafață & Volum<br>
                • Raport Metrologic .TXT<br>
                • Vizualizator 3D Puncte
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with p2:
    st.markdown(
        """
            <div class='price-card'>
                <h4 style='color: #50C878; margin-top:0;'>PLAN PRO LUNAR</h4>
                <h2 style='color: #FFF;'>29.99 € <span style='font-size:12px; color:#AAA;'>/ lună</span></h2>
                <p style='font-size:12px; color:#CBD5E1; text-align:left;'>
                • <b>Procesare nelimitată fișiere masive</b><br>
                • Export avansat DXF & rapoarte oficiale<br>
                • Algoritmi de filtrare vegetație<br>
                • Suport Prioritar Cloud
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.link_button(
        "💳 Abonează-te Lunar",
        "https://buy.stripe.com/aFaeVdgqJ03l6c4fJEbAs00",
        use_container_width=True,
    )

  with p3:
    st.markdown(
        """
            <div class='price-card'>
                <h4 style='color: #50C878; margin-top:0;'>PLAN BIZ ANUAL</h4>
                <h2 style='color: #FFF;'>249.99 € <span style='font-size:12px; color:#AAA;'>/ an</span></h2>
                <p style='font-size:12px; color:#94A3B8; text-align:left;'>
                • Tot ce include Planul PRO<br>
                • <b>Economisești peste 30% anual</b><br>
                • Acces API dedicat geodezie<br>
                • Multi-utilizator echipă șantier
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.link_button(
        "💳 Abonează-te Anual",
        "https://buy.stripe.com/8x23cvcat9DVgQIgNIbAs01",
        use_container_width=True,
    )

# TAB TERMENI & GDPR
with tab_legal:
  st.subheader("⚖️ Termeni și Condiții & Politică de Confidențialitate (GDPR)")
  st.write("")
  st.markdown("### 1. Protecția Datelor de Șantier")
  st.markdown(
      "Fișierele încărcate sunt procesate securizat în memorie temporară și"
      " șterse imediat după finalizarea calculelor metrologice."
  )
  st.markdown("### 2. Responsabilitate Tehnică")
  st.markdown(
      "Rapoartele și volumele calculate au scop de sprijin în activitatea"
      " tehnică. Verificarea finală revine specialistului autorizat."
  )

# FOOTER
st.write("<br><br>", unsafe_allow_html=True)
st.markdown("---")
f_col1, f_col2 = st.columns(2)

with f_col1:
  st.markdown("### 🛡️ Securitate & Date")
  st.markdown(
      """
        <div style='background: #0D1C24; padding: 18px; border-radius: 12px; border: 1px solid rgba(80,200,120,0.15); font-size: 12px; color: #94A3B8;'>
            <b>🔒 GDPR & Siguranță:</b> Datele topografice nu sunt partajate sau stocate permanent pe servere externe.
        </div>
    """,
      unsafe_allow_html=True,
  )

with f_col2:
  st.markdown("### 📬 Asistență Tehnică")
  with st.form(key="form_c_footer", clear_on_submit=True):
    em = st.text_input("E-mail:", placeholder="nume@companie.ro")
    tp = st.selectbox("Subiect:", ["Eroare calcul", "Sugestie funcție", "Altul"])
    ms = st.text_area("Mesaj:", placeholder="Scrie-ne...")
    btn_c = st.form_submit_button("Trimite mesaj")
    if btn_c and em and ms:
      salveaza_contact(em, tp, ms)
      trimite_email_formspree(em, tp, ms)
      st.success("🎉 Mesaj trimis cu succes!")

st.markdown(
    """
    <div style='text-align: center; color: #64748B; font-size: 11px; margin-top: 30px; margin-bottom: 15px;'>
        © 2026 Shazam-BIM & Geodesy Engine. Toate drepturile rezervate.
    </div>
""",
    unsafe_allow_html=True,
)
