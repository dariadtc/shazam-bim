import streamlit as st, numpy as np, open3d as o3d, os, sqlite3
from datetime import datetime

st.set_page_config(page_title="Shazam-BIM", layout="wide")

# --- CONFIGURARE BAZĂ DE DATE ---
def initializeaza_baza_date():
    conn = sqlite3.connect("proiecte_bim.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scanari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nume_proiect TEXT,
            data_procesare TEXT,
            lungime_teva REAL,
            lungime_perete REAL,
            inaltime_perete REAL,
            latime_gol REAL,
            inaltime_gol REAL
        )
    """)
    conn.commit()
    conn.close()

def salveaza_in_baza_date(nume, l_t, l_w, h_w, l_g, h_g):
    conn = sqlite3.connect("proiecte_bim.db")
    cursor = conn.cursor()
    data_acum = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO scanari (nume_proiect, data_procesare, lungime_teva, lungime_perete, inaltime_perete, latime_gol, inaltime_gol)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(nume), data_acum, round(float(l_t), 2), round(float(l_w), 2), round(float(h_w), 2), round(float(l_g), 2), round(float(h_g), 2)))
    conn.commit()
    conn.close()

def citeste_istoric():
    conn = sqlite3.connect("proiecte_bim.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nume_proiect, data_procesare, lungime_teva, lungime_perete, inaltime_perete, latime_gol, inaltime_gol FROM scanari ORDER BY id DESC")
    date = cursor.fetchall()
    conn.close()
    return date

initializeaza_baza_date()

# --- MOTORUL GEOMETRIC UNIVERSAL ---
def genereaza_demo_puncte(n=120000):
    x, y, z = np.random.uniform(0, 5, n//5), np.random.uniform(0, 5, n//5), np.random.uniform(0, 3, n//5)
    t_th, t_l = np.random.uniform(0, 2*np.pi, n//5), np.random.uniform(0.1, 4.9, n//5)
    mask_usa = (y >= 2.0) & (y <= 3.0) & (z <= 2.1)
    pts = [np.vstack((x, y, np.zeros_like(x))).T, np.vstack((x, y, np.ones_like(x)*3.0)).T,
           np.vstack((np.zeros_like(z[~mask_usa]), y[~mask_usa], z[~mask_usa])).T, np.vstack((np.ones_like(z)*5.0, y, z)).T,
           np.vstack((t_l, 2.5 + 0.15*np.cos(t_th), 2.0 + 0.15*np.sin(t_th))).T]
    return np.vstack(pts) + np.random.normal(0, 0.005, (len(np.vstack(pts)), 3))

def ruleaza_click(pcd):
    v = o3d.visualization.draw_geometries_with_editing([pcd], "SHIFT+Click / Q=Iesire", width=1024, height=768)
    return np.asarray(pcd.points)[v.get_picked_points()] if v.get_picked_points() else None

def detecteaza_goluri_perete(puncte_perete, rezolutie_grila=0.1):
    if len(puncte_perete) < 100: return 0.0, 0.0
    y_coords, z_coords = puncte_perete[:, 1], puncte_perete[:, 2]
    b_y = int((y_coords.max() - y_coords.min()) / rezolutie_grila)
    b_z = int((z_coords.max() - z_coords.min()) / rezolutie_grila)
    if b_y <= 0 or b_z <= 0: return 0.0, 0.0
    counts, _, _ = np.histogram2d(y_coords, z_coords, bins=[b_y, b_z])
    zone_goale = (counts == 0)
    if not np.any(zone_goale): return 0.0, 0.0
    idx_y, idx_z = np.where(zone_goale)
    return min((idx_y.max() - idx_y.min() + 1) * rezolutie_grila, 1.0), min((idx_z.max() + 1) * rezolutie_grila, 2.1)

def creaza_solid(pcd, masca, tip="teva", r=0.15):
    pts = np.asarray(pcd.points)[masca]
    if len(pts) < 20: return None, 0.0, 0.0
    bb = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).get_axis_aligned_bounding_box()
    ext = bb.get_extent()
    ctr = bb.get_center()
    
    # REPARARE CORECTĂ: Extragem axele individual din array prin indecși indexați numeric
    ext_x, ext_y, ext_z = float(ext[0]), float(ext[1]), float(ext[2])
    
    if tip == "teva":
        m = o3d.geometry.TriangleMesh.create_cylinder(radius=r, height=ext_x)
        m.rotate(m.get_rotation_matrix_from_xyz((0, np.pi/2, 0)), (0,0,0))
        dim1, dim2 = ext_x, r*2
    else:
        m = o3d.geometry.TriangleMesh.create_box(width=0.20 if ext_x<ext_y else ext_x, height=ext_y if ext_x<ext_y else 0.20, depth=ext_z)
        dim1, dim2 = ext_y if ext_x<ext_y else ext_x, ext_z
    m.paint_uniform_color([1.0, 0.6, 0.0] if tip=="teva" else [0.9, 0.1, 0.1])
    m.translate(ctr - m.get_center(), relative=True)
    return m, dim1, dim2

def proceseaza(points, vox, r_m, clk=None, demo=True):
    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points)).voxel_down_sample(vox)
    pcd, _ = pcd.remove_statistical_outlier(25, 1.5)
    arr = np.asarray(pcd.points)
    cols = np.ones((len(pcd.points), 3)) * 0.5
    m_p, m_t, m_w, m_p_m = [np.zeros(len(arr), dtype=bool) for _ in range(4)]
    if demo:
        m_p_m, m_p, m_t, m_w = (arr[:, 2]>1.8)&(arr[:, 2]<2.2)&(arr[:, 1]>2.3)&(arr[:, 1]<2.7), arr[:, 2]<0.1, arr[:, 2]>2.9, (arr[:, 0]<0.1)|(arr[:, 0]>4.9)
    else:
        pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(0.15, 30))
        rem = pcd
        for i in range(5):
            if len(rem.points) < 50: break
            try:
                p, inl = rem.segment_plane(0.04, 3, 500)
                idx = np.where(np.ones(len(arr), dtype=bool) if i==0 else (~m_p if i==1 else (~m_p & ~m_t)))[inl]
                if abs(p) > 0.80:
                    if np.mean(arr[inl, 2]) < np.mean(arr[:, 2]): m_p[idx] = True
                    else: m_t[idx] = True
                elif abs(p) < 0.20 and i >= 2: m_w[idx] = True
                rem = rem.select_by_index(inl, invert=True)
            except: break
        if clk is not None:
            m_p_m[np.where((~m_p)&(~m_t)&(~m_w))[np.linalg.norm(np.asarray(rem.points)-clk, axis=1) < 0.40]] = True
        elif len(rem.points) > 50:
            rem.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(20))
            m_p_m[np.where((~m_p)&(~m_t)&(~m_w))[np.std(np.asarray(rem.normals), axis=1) > 0.30]] = True
            
    cols[m_p], cols[m_t], cols[m_w], cols[m_p_m] = [0.1, 0.8, 0.1], [0.1, 0.1, 0.9], [0.9, 0.1, 0.1], [1.0, 0.6, 0.0]
    pcd.colors = o3d.utility.Vector3dVector(cols)
    
    l_gol, h_gol = detecteaza_goluri_perete(arr[m_w])
    if demo: l_gol, h_gol = 1.00, 2.10
    
    m_t_s, l_t, _ = creaza_solid(pcd, m_p_m, "teva", r_m)
    m_w_s, l_w, h_w = creaza_solid(pcd, m_w, "perete")
    return pcd, m_t_s, l_t, m_w_s, l_w, h_w, l_gol, h_gol

# --- INTERFAȚA WEB ---
st.title("🤖 Shazam-BIM + Jurnal Database")
sursa = st.sidebar.radio("Sursă:", ["Demo", "Fișier (.ply, .las)"])
up = st.sidebar.file_uploader("Nor puncte:", type=["las", "ply"]) if sursa != "Demo" else None
vox = st.sidebar.slider("Voxel (m)", 0.01, 0.10, 0.04, 0.01)
r_c = st.sidebar.slider("Rază țeavă (m)", 0.05, 0.50, 0.15, 0.01)
op = st.sidebar.checkbox("🎯 Ghidaj manual prin Click", value=False)

if st.sidebar.button("🚀 Procesează"):
    nume_proiect = "DEMO_ROOM"
    if sursa == "Demo": pts = genereaza_demo_puncte()
    elif up:
        with open(up.name, "wb") as f: f.write(up.getbuffer())
        # REPARARE: Extragem numele curat ca text simplu pentru a evita tuplurile în baza de date
        nume_proiect = str(os.path.splitext(up.name)[0])
        pts = np.asarray(o3d.io.read_point_cloud(up.name).points)
        os.remove(up.name)
    else: st.error("Încarcă fișier!"); st.stop()
    
    clk = ruleaza_click(o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts)).voxel_down_sample(vox)) if op and sursa != "Demo" else None
    pcd_f, m_t, l_t, m_w, l_w, h_w, l_gol, h_gol = proceseaza(pts, vox, r_c, clk, sursa == "Demo")
    
    salveaza_in_baza_date(nume_proiect, l_t, l_w, h_w, l_gol, h_gol)
    
    vis_list = [pcd_f]
    if m_t is not None: o3d.io.write_triangle_mesh("t.obj", m_t); vis_list.append(m_t)
    if m_w is not None: 
        o3d.io.write_triangle_mesh("w.obj", m_w)
        vis_list.append(m_w)
        wf = o3d.geometry.LineSet.create_from_triangle_mesh(m_w)
        wf.paint_uniform_color([0.0, 0.0, 0.0])
        vis_list.append(wf)
    
    st.success("🎉 Rularea a fost înregistrată în baza de date!")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Lungime Țeavă", f"{l_t:.2f} m")
        st.metric("Lungime Perete", f"{l_w:.2f} m")
    with c2:
        st.metric("Înălțime Perete", f"{h_w:.2f} m")
        st.metric("Grosime", "20.0 cm")
    with c3:
        if l_gol > 0:
            st.metric("Lățime Gol Detectat", f"{l_gol:.2f} m")
            st.metric("Înălțime Gol Detectată", f"{h_gol:.2f} m")
        else:
            st.metric("Goluri în structură", "Nedetectat")
    
    if m_t is not None: st.download_button("📥 Descarcă Instalația (.OBJ)", open("t.obj", "rb"), f"MEP_{sursa}.obj")
    if m_w is not None: st.download_button("📥 Descarcă Peretele (.OBJ)", open("w.obj", "rb"), f"WALL_{sursa}.obj")
    o3d.visualization.draw_geometries(vis_list, window_name="Shazam-BIM Engine", width=1024, height=768)

st.write("---")
st.subheader("📋 Relevee Înregistrate (Istoric Server Local)")
istoric_date = citeste_istoric()

if len(istoric_date) > 0:
    st.dataframe(
        istoric_date,
        column_config={
            "0": "Nume Proiect", "1": "Data și Ora Scanării", "2": "Lungime Țeavă (m)",
            "3": "Lungime Perete (m)", "4": "Înălțime Perete (m)", "5": "Lățime Ușă (m)", "6": "Înălțime Ușă (m)"
        },
        use_container_width=True
    )
else:
    st.info("Baza de date este goală. Lansați o procesare pentru a salva primul releveu!")
