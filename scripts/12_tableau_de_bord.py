"""12 - Tableau de bord accessible (HTML autonome) : carte, détail par commune, tableau de données.
Accessibilité : police Atkinson Hyperlegible (conçue pour la basse vision), palette sûre pour les daltoniens
(Okabe-Ito) + motifs optionnels, contrastes AA, navigation clavier, tableau alternatif à la carte,
annonces vocales (aria-live), mode sombre, mouvement réduit respecté."""
import json, numpy as np, pandas as pd, sys
sys.path.insert(0, "scripts")
from referentiel import PASSAGE_COG

BLOCS = ["GAUCHE", "CENTRE", "DROITE", "EXTREME_DROITE"]
df = pd.read_csv("data_clean/table_modelisation.csv", dtype={"code_commune": str})
pred = pd.read_csv("data_clean/predictions_2027_2029.csv", dtype={"code_commune": str})
lib = pd.read_csv("data_raw/legi2024_t1_isere_communes.csv", dtype=str).drop_duplicates("com").set_index("com").libelle
ctx = pd.read_csv("data_clean/contexte_commune_annee.csv", dtype={"code_commune": str})
c25 = ctx[ctx.annee == 2025].set_index("code_commune")
typo = pd.read_csv("data_clean/typologie_communes.csv", dtype={"code_commune": str}).set_index("code_commune").groupe

vues = {}
for s in ["PRES_2017", "LEGI_2017", "EURO_2019", "PRES_2022", "LEGI_2022", "LEGI_2024"]:
    g = df[df.scrutin == s].set_index("code_commune")
    vues[s] = {c: [round(100 * r[f"part_{b}"], 1) for b in BLOCS] + [round(100 * r.participation, 1), BLOCS.index(r.bloc_en_tete)] for c, r in g.iterrows()}
for a in (2027, 2028, 2029):
    g = pred[pred.annee == a].set_index("code_commune")
    vues[f"PROJ_{a}"] = {c: [round(100 * r[b], 1) for b in BLOCS] + [None, BLOCS.index(r.bloc_en_tete_predit)] for c, r in g.iterrows()}
# Noms lisibles des groupes de la typologie (script 10), déduits de leur profil
prof = pd.read_csv("data_clean/typologie_communes_profils.csv", index_col=0)
noms_typo = {int(prof.population.idxmax()): "Pôle urbain", int(prof.logements_hab.idxmax()): "Petite commune de montagne ou rurale"}
noms_typo.update({int(i): "Bourg ou commune périurbaine" for i in prof.index if int(i) not in noms_typo})
typo = typo.map(noms_typo)
communes = {c: {"n": lib.get(c, c), "p": int(c25.loc[c, "insee_pop"]), "nv": int(round(c25.loc[c, "niveau_vie_median"])),
                "ch": round(100 * c25.loc[c, "taux_chomage"], 1), "t": typo.get(c, "")} for c in c25.index}

# Contours -> chemins SVG projetés (équirectangulaire corrigée), coordonnées arrondies
geo = json.load(open("data_raw/contours_communes_isere.geojson"))
k = np.cos(np.radians(45.2)); pts = []
for f in geo["features"]:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for p in polys: pts += p[0]
xs, ys = np.array([p[0] for p in pts]) * k, np.array([p[1] for p in pts])
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); W = 600; S = W / (x1 - x0); H = (y1 - y0) * S
chemins = []
for f in geo["features"]:
    code = PASSAGE_COG.get(f["properties"]["code"], f["properties"]["code"])
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    d = ""
    for p in polys:
        ring = p[0][::2] if len(p[0]) > 40 else p[0]
        d += "M" + "L".join(f"{(x * k - x0) * S:.1f},{(y1 - y) * S:.1f}" for x, y in ring) + "Z"
    chemins.append([code, d])
DATA = json.dumps({"vues": vues, "communes": communes, "chemins": chemins, "w": W, "h": round(H)}, ensure_ascii=False, separators=(",", ":"))

HTML = open("scripts/tableau_de_bord_gabarit.html", encoding="utf-8").read().replace("/*__DONNEES__*/", DATA)
open("tableau_de_bord/tableau_de_bord_isere.html", "w", encoding="utf-8").write(HTML)
print("ok", round(len(HTML) / 1e6, 2), "Mo")
