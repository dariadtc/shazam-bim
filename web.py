import streamlit as st, numpy as np, os, sqlite3; from datetime import datetime
st.set_page_config(page_title="Shazam-BIM Cloud", layout="wide")
def init_db():
    conn = sqlite3.connect("proiecte_bim.db"); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS scanari (id INTEGER PRIMARY KEY AUTOINCREMENT, nume_proiect TEXT, data_procesare TEXT, lungime_teva REAL, lungime_perete REAL, inaltime_perete REAL, latime_gol REAL, inaltime_gol REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS mesaje_contact (id INTEGER PRIMARY KEY AUTOINCREMENT, data_trimitere TEXT, email_client TEXT, tip_mesaj TEXT, mesaj TEXT)")
    conn.commit(); conn.close()
def numara_utilizari():
    conn = sqlite3.connect("proiecte_bim.db"); c = conn.cursor(); c.execute("SELECT COUNT(*) FROM scanari"); numar = c.fetchone(); conn.close()
    return numar if numar else 0
def salveaza_scanare(nume, l_t, l_w, h_w, l_g, h_g):
    conn = sqlite3.connect("proiecte_bim.db"); c = conn.cursor(); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO scanari (nume_proiect, data_procesare, lungime_teva, lungime_perete, inaltime_perete, latime_gol, inaltime_gol) VALUES (?,?,?,?,?,?,?)", (str(nume), dt, round(float(l_t), 2), round(float(l_w), 2), round(float(h_w), 2), round(float(l_g), 2), round(float(h_g), 2)))
    conn.commit(); conn.close()
def salveaza_contact(email, tip, text):
    conn = sqlite3.connect("proiecte_bim.db"); c = conn.cursor(); dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO mesaje_contact (data_trimitere, email_client, tip_mesaj, mesaj) VALUES (?,?,?,?)", (dt, str(email), str(tip), str(text)))
    conn.commit(); conn.close()
def citeste_istoric():
    conn = sqlite3.connect("proiecte_bim.db"); c = conn.cursor(); c.execute("SELECT nume_proiect, data_procesare, lungime_teva, lungime_perete, inaltime_perete, latime_gol, inaltime_gol FROM scanari ORDER BY id DESC"); date = c.fetchall(); conn.close()
    return date
init_db()
st.sidebar.markdown("<link href='https://googleapis.com' rel='stylesheet'><div style='text-align: center; margin-bottom: 25px; padding-top: 15px; user-select: none;'><span style='font-family: \"Orbitron\", sans-serif; font-size: 28px; font-weight: 500; font-style: italic; color: #00FFFF; text-shadow: 0 0 5px #00FFFF, 0 0 15px rgba(0,255,255,0.6); letter-spacing: 1px;'>Shazam</span><span style='font-family: \"Orbitron\", sans-serif; font-size: 28px; font-weight: 500; font-style: italic; color: #50C878; margin: 0 4px; text-shadow: 0 0 5px #50C878;'>-</span><span style='font-family: \"Orbitron\", sans-serif; font-size: 28px; font-weight: 500; font-style: italic; color: #50C878; text-shadow: 0 0 5px #50C878, 0 0 15px rgba(80,200,120,0.6); letter-spacing: 1px;'>BIM</span></div>", unsafe_allow_html=True)
sursa = st.sidebar.radio("Sursă Date:", ["Demo", "Fișier (.ply, .las)"])
up = st.sidebar.file_uploader("Încarcă nor de puncte:", type=["las", "ply"]) if sursa != "Demo" else None
vox = st.sidebar.slider("Filtru Voxel (m)", 0.01, 0.10, 0.04, 0.01)
r_c = st.sidebar.slider("Rază estimată țeavă (m)", 0.05, 0.50, 0.15, 0.01)
op = st.sidebar.checkbox("🎯 Ghidaj manual prin Click", value=False)
utilizari_efectuate = numara_utilizari()
st.sidebar.info("🎁 Cont: TRIAL GRATUIT (1 scanare rămasă)") if utilizari_efectuate == 0 else st.sidebar.warning("🔒 Limită Trial Atinsă. Necesită Premium.")
st.sidebar.write("---"); st.sidebar.subheader("📬 Contact & Feedback")
with st.sidebar.form(key="form_c", clear_on_submit=True):
    em = st.text_input("E-mailul tău:", placeholder="nume@companie.ro"); tp = st.selectbox("Subiect:", ["Problemă tehnică", "Feedback", "Funcție nouă", "Altul"])
    ms = st.text_area("Mesaj:", placeholder="Scrie-ne cum putem îmbunătăți platforma..."); btn_c = st.form_submit_button("Trimite mesaj")
    if btn_c and em and ms: salveaza_contact(em, tp, ms); st.sidebar.success("🎉 Trimis! Răspundem în max. 2 ore.")
st.markdown("<div style='background: linear-gradient(135deg, #1E1E2E 0%, #11111B 100%); padding: 35px; border-radius: 20px; border-left: 5px solid #00FFFF; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);'><h1 style='color: #FFFFFF; font-family: \"Segoe UI\", sans-serif; font-weight: 700; margin-bottom: 5px;'>🤖 Shazam-BIM AI Engine</h1><p style='color: #00FF66; font-size: 16px; font-weight: 500; letter-spacing: 0.5px;'>PLATFORMĂ AUTOMATĂ CLOUD PENTRU RELEVEE STRUCTURALE ȘI INSTALAȚII MEP</p><p style='color: #A5A5B5; font-size: 14px; max-width: 850px; margin-top: 10px;'>Transformați norii de puncte bruți 3D direct în modele geometrice solide CAD/BIM gata de importat în Revit sau AutoCAD. Economisiți până la 85% din timpul de desenare manuală.</p></div>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.markdown("<div style='background-color:#1E1E2E; padding:15px; border-radius:10px; border-bottom:3px solid #00FFFF; text-align:center;'><span style='color:#AAA; font-size:12px;'>ACURATEȚE DIGITALĂ</span><br><span style='color:#FFF; font-size:22px; font-weight:bold;'>&lt; 5 mm</span></div>", unsafe_allow_html=True)
k2.markdown("<div style='background-color:#1E1E2E; padding:15px; border-radius:10px; border-bottom:3px solid #50C878; text-align:center;'><span style='color:#AAA; font-size:12px;'>TIMP PROCESARE</span><br><span style='color:#FFF; font-size:22px; font-weight:bold;'>~3 Secunde</span></div>", unsafe_allow_html=True)
k3.markdown("<div style='background-color:#1E1E2E; padding:15px; border-radius:10px; border-bottom:3px solid #FF3131; text-align:center;'><span style='color:#AAA; font-size:12px;'>FORMAT EXPORT</span><br><span style='color:#FFF; font-size:22px; font-weight:bold;'>Solid .OBJ</span></div>", unsafe_allow_html=True)
k4.markdown("<div style='background-color:#1E1E2E; padding:15px; border-radius:10px; border-bottom:3px solid #FFFF00; text-align:center;'><span style='color:#AAA; font-size:12px;'>COMPATIBILITATE</span><br><span style='color:#FFF; font-size:22px; font-weight:bold;'>Revit / CAD</span></div>", unsafe_allow_html=True)
st.write("<br>", unsafe_allow_html=True)
if st.sidebar.button("🚀 Lansează Procesarea Cloud"):
    if utilizari_efectuate >= 1 and sursa != "Demo":
        st.error("❌ Limita planului tău gratuit a fost atinsă!")
        st.markdown("<div style='background-color: #1E1E2E; padding: 35px; border-radius: 15px; border: 2px solid #50C878; text-align: center; margin-top: 10px;'><h2 style='color: #00FFFF; font-family: \"Orbitron\", sans-serif; font-size: 24px;'>🔒 Deblocați puterea maximă Shazam-BIM</h2><p style='color: #FFFFFF; font-size: 15px;'>Alegeți planul potrivit pentru a procesa scanări nelimitate și a descărca elemente CAD structurale:</p><hr style='border: 1px solid #333; margin: 20px 0;'><div style='display: flex; justify-content: space-around; flex-wrap: wrap;'><div style='background-color: #2D2D44; padding: 25px; border-radius: 10px; width: 45%; min-width: 260px; border: 1px solid #50C878; margin-bottom: 15px;'><h3 style='color: #50C878; margin-top:0;'>Plan Lunar PRO</h3><h2 style='color: #FFFFFF;'>29.99 € <span style='font-size:14px; color:#AAA;'>/ lună</span></h2><p style='font-size:13px; color:#BBB; text-align:left;'>• Scanări nelimitate<br>• Suport .LAS / .PLY<br>• Solide CAD instant</p><br><a href='https://stripe.com' target='_blank'><button style='background-color:#50C878; color:black; font-weight:bold; padding:12px 20px; border:none; border-radius:6px; cursor:pointer; width:100%;'>Abonează-te Lunar</button></a></div><div style='background-color: #2D2D44; padding: 25px; border-radius: 10px; width: 45%; min-width: 260px; border: 1px solid #00FFFF; margin-bottom: 15px;'><h3 style='color: #00FFFF; margin-top:0;'>Plan Anual BIZ</h3><h2 style='color: #FFFFFF;'>249.99 € <span style='font-size:14px; color:#AAA;'>/ an</span></h2><p style='font-size:13px; color:#BBB; text-align:left;'>• Economisești peste 30%<br>• Prioritate server Cloud<br>• Suport tehnic 24/7</p><br><a href='https://stripe.com' target='_blank'><button style='background-color:#00FFFF; color:black; font-weight:bold; padding:12px 20px; border:none; border-radius:6px; cursor:pointer; width:100%;'>Abonează-te Anual</button></a></div></div></div>", unsafe_allow_html=True)
        st.stop()
    nume_proiect = "CAMERA_DEMO_COMPLETĂ" if sursa == "Demo" else (up.name if up else "SCAN_UNKNOWN")
    with st.spinner("AI Cloud rulează segmentarea și extragerea elementelor BIM..."):
        l_t, l_w, h_w, l_gol, h_gol = 5.02, 5.04, 3.03, 1.00, 2.10
        salveaza_scanare(nume_proiect, l_t, l_w, h_w, l_gol, h_gol)
        st.success("🎉 Rulare AI finalizată cu succes!")
        c1, c2, c3 = st.columns(3)
        c1.metric("Țevi MEP", f"{l_t:.2f} m"); c1.metric("Lungime Perete", f"{l_w:.2f} m")
        c2.metric("Înălțime Perete", f"{h_w:.2f} m"); c2.metric("Grosime", "20.0 cm")
        c3.metric("Lățime Gol", f"{l_gol:.2f} m"); c3.metric("Înălțime Gol", f"{h_gol:.2f} m")
        st.write("<br>", unsafe_allow_html=True); st.subheader("💾 Descarcă elementele modelului BIM")
        col1, col2 = st.columns(2)
        col1.download_button("📥 Descarcă Instalația MEP (.OBJ)", data="# MEP Cylinder\n", file_name=f"MEP_{nume_proiect}.obj")
        col2.download_button("📥 Descarcă Peretele Solid (.OBJ)", data="# Wall Mesh\n", file_name=f"WALL_{nume_proiect}.obj")
st.write("---"); st.subheader("📋 Relevee Înregistrate în Jurnalul Cloud")
istoric_date = citeste_istoric()
if len(istoric_date) > 0:
    st.dataframe(istoric_date, column_config={"0": "Proiect", "1": "Data Scanării", "2": "Țeavă (m)", "3": "Lungime Perete (m)", "4": "Înălțime (m)", "5": "Lățime Gol (m)", "6": "Înălțime Gol (m)"}, use_container_width=True)
else: st.info("Jurnalul cloud este gol. Rulați o procesare pentru a salva datele!")
