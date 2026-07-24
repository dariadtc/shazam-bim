import sys
import os
import laspy
import numpy as np
from scipy.spatial import Delaunay

def incarca_nor_puncte(filepath):
    """
    Încarcă coordonatele X, Y, Z dintr-un fișier LiDAR (.las/.laz) 
    sau dintr-un fișier text ASCII (.xyz, .pts, .txt).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"❌ Fișierul nu a fost găsit: {filepath}")
    
    ext = os.path.splitext(filepath)[1].lower()
    print(f"📂 Se citește fișierul '{os.path.basename(filepath)}'...")

    if ext in [".las", ".laz"]:
        las = laspy.read(filepath)
        x = np.array(las.x, dtype=np.float64)
        y = np.array(las.y, dtype=np.float64)
        z = np.array(las.z, dtype=np.float64)
    elif ext in [".xyz", ".pts", ".txt"]:
        data = np.loadtxt(filepath)
        if data.shape[1] < 3:
            raise ValueError("Fișierul text trebuie să conțină cel puțin 3 coloane (X, Y, Z).")
        x = data[:, 0]
        y = data[:, 1]
        z = data[:, 2]
    else:
        raise ValueError(f"Format de fișier neacceptat: {ext}. Folosiți .las, .laz, .xyz, .pts")

    return x, y, z

def calculeaza_mdt_si_suprafata(x, y):
    """
    Generează rețeaua de tinete (Triangulație Delaunay 2D) și 
    calculează suprafața proiectată (2D) și suprafața reală (3D) a terenului.
    """
    print("⚙️ Se generează rețeaua de tinete (Triangulație Delaunay)...")
    points_2d = np.column_stack((x, y))
    tri = Delaunay(points_2d)

    # Extragerea coordonatelor vârfurilor fiecărui triunghi
    triangles = points_2d[tri.simplices]
    x1, y1 = triangles[:, 0, 0], triangles[:, 0, 1]
    x2, y2 = triangles[:, 1, 0], triangles[:, 1, 1]
    x3, y3 = triangles[:, 2, 0], triangles[:, 2, 1]

    # Suprafața 2D a fiecărui triunghi prin formula lui Gauss (Shoelace)
    arii_2d = 0.5 * np.abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    suprafata_2d_totala = np.sum(arii_2d)

    return tri, suprafata_2d_totala

def calculeaza_volum_prisme(x, y, z, tri):
    """
    Calculează volumul prin metoda prismelor raportate la planul de referință (Z_min).
    """
    print("📐 Se calculează volumul prin prisme topografice...")
    z_min = np.min(z)
    
    # Cotele pe z pentru cele 3 vârfuri ale fiecărui triunghi din rețea
    z_tri = z[tri.simplices]
    medie_z_tri = np.mean(z_tri, axis=1)
    
    # Înălțimea medie a fiecărei prisme față de cota de bază
    inaltimi_relative = medie_z_tri - z_min

    # Recalculăm ariile 2D pentru triunghiurile din structura Delaunay
    points_2d = np.column_stack((x, y))
    triangles = points_2d[tri.simplices]
    arii_2d = 0.5 * np.abs(
        triangles[:, 0, 0] * (triangles[:, 1, 1] - triangles[:, 2, 1]) +
        triangles[:, 1, 0] * (triangles[:, 2, 1] - triangles[:, 0, 1]) +
        triangles[:, 2, 0] * (triangles[:, 0, 1] - triangles[:, 1, 1])
    )

    volum_total = np.sum(arii_2d * inaltimi_relative)
    return volum_total, z_min

def ruleaza_analiza_geodezica(filepath):
    """
    Funcția principală care orchestrează fluxul de calcul metrologic.
    """
    try:
        x, y, z = incarca_nor_puncte(filepath)
        n_puncte = len(x)
        
        print(f"\n================ STATISTICI PRELIMINARE ================")
        print(f"• Număr total puncte procesate : {n_puncte:,}")
        print(f"• Altimetrie Z (Min / Max)      : {np.min(z):.3f} m / {np.max(z):.3f} m")
        print(f"• Extindere în plan (ΔX / ΔY)   : {np.ptp(x):.3f} m / {np.ptp(y):.3f} m")
        print(f"=========================================================\n")

        # Rulație funcție 1: MDT și Suprafață
        tri, suprafata_2d = calculeaza_mdt_si_suprafata(x, y)

        # Rulație funcție 2: Volumetrie prin prisme
        volum, cota_referinza = calculeaza_volum_prisme(x, y, z, tri)

        print(f"================ RAPORT METROLOGIC FINAL ================")
        print(f"📐 Suprafață Proiectată 2D     : {suprafata_2d:,.2f} mp")
        print(f"📏 Cota de Referință (Bază Z)  : {cota_referinza:.3f} m")
        print(f"📦 Volum Brut Calculat (Prisme): {volum:,.2f} mc")
        print(f"=========================================================\n")

        return {
            "puncte": n_puncte,
            "suprafata_mp": suprafata_2d,
            "volum_mc": volum,
            "cota_baza": cota_referinza
        }

    except Exception as e:
        print(f"❌ Eroare în timpul procesării geodezice: {e}")
        return None

if __name__ == "__main__":
    # Exemplu de apel din linie de comandă sau rulare directă
    if len(sys.argv) > 1:
        fisier_intrare = sys.argv[1]
    else:
        # Pune aici calea ta de test locală dacă rulezi direct din IDE
        fisier_intrare = "scanare_test.las" 
    
    if os.path.exists(fisier_intrare):
        ruleaza_analiza_geodezica(fisier_intrare)
    else:
        print(f"⚠️ Fișierul de test '{fisier_intrare'}' nu există. Specificați calea corectă ca argument în consolă.")
