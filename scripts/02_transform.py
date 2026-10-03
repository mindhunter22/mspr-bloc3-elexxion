"""02 - Transformation : harmonisation des 6 scrutins, rattachement aux blocs politiques,
passage au Code Officiel Géographique (COG) 2025, agrégation par commune."""
import pandas as pd

RAW = "data_source"  # fichiers nationaux téléchargés sur data.gouv.fr (voir README)

from referentiel import PASSAGE_COG, BLOC_NUANCE, BLOC_PRES, BLOC_EURO2019

def norm(df, scrutin, annee, type_scrutin):
    df = df.copy()
    df["code_commune"] = df["code_commune"].replace(PASSAGE_COG)
    df["scrutin"], df["annee"], df["type_scrutin"] = scrutin, annee, type_scrutin
    return df

frames, particip = [], []

# 2017 présidentielle T1 / 2017 législatives T1 / 2019 européennes (fichiers normalisés)
for f, sc, an, ty, key in [
    ("2017-presidentielle-1", "PRES_2017", 2017, "PRES", "nom"),
    ("2017-legislatives-1", "LEGI_2017", 2017, "LEGI", "nuance"),
    ("2019-europeennes", "EURO_2019", 2019, "EURO", "nom_liste"),
]:
    d = pd.read_csv(f"{RAW}/{f}_par_commune_long.csv.gz", dtype={"departement": str, "commune": str})
    d = d[d.departement == "38"].copy()
    d["code_commune"] = "38" + d.commune
    if key == "nom":
        d["bloc"] = d.nom.map(BLOC_PRES)
    elif key == "nuance":
        d["bloc"] = d.nuance.map(BLOC_NUANCE)
    else:
        d["bloc"] = d.nom_liste.map(BLOC_EURO2019).fillna("AUTRES")
    d = norm(d, sc, an, ty)
    # participation : une ligne par commune (en 2017 législatives, une commune peut être sur 2 circos -> somme par circo unique)
    p = d.drop_duplicates(["code_commune", "commune", "inscrits", "votants"])[["code_commune", "inscrits", "votants", "exprimes"]]
    particip.append(p.groupby("code_commune").sum().reset_index().assign(scrutin=sc))
    frames.append(d[["code_commune", "scrutin", "annee", "type_scrutin", "bloc", "voix"]])

# 2022 présidentielle T1 (par bureau de vote -> commune)
d = pd.read_csv("data_raw/pres2022_t1_isere_bureaux.csv", dtype={"com": str, "bureau": str})
d["code_commune"] = "38" + d.com.str.zfill(3)
d["bloc"] = d.nom.map(BLOC_PRES)
d = norm(d, "PRES_2022", 2022, "PRES")
p = d.drop_duplicates(["code_commune", "bureau"])[["code_commune", "inscrits", "votants", "exprimes"]]
particip.append(p.groupby("code_commune").sum().reset_index().assign(scrutin="PRES_2022"))
frames.append(d[["code_commune", "scrutin", "annee", "type_scrutin", "bloc", "voix"]])

# 2022 et 2024 législatives T1 (par commune, éventuellement découpée en plusieurs circonscriptions)
for f, sc, an, circo in [("legi2022_t1_isere_communes.csv", "LEGI_2022", 2022, True),
                          ("legi2024_t1_isere_communes.csv", "LEGI_2024", 2024, False)]:
    d = pd.read_csv(f"data_raw/{f}", dtype=str)
    d["code_commune"] = ("38" + d.com.str.zfill(3)) if circo else d.com
    for c in ["inscrits", "votants", "exprimes", "voix"]:
        d[c] = pd.to_numeric(d[c])
    d["bloc"] = d.nuance.map(BLOC_NUANCE)
    d = norm(d, sc, an, "LEGI")
    keys = ["code_commune", "circo"] if circo else ["code_commune"]
    p = d.drop_duplicates(keys)[["code_commune", "inscrits", "votants", "exprimes"]]
    particip.append(p.groupby("code_commune").sum().reset_index().assign(scrutin=sc))
    frames.append(d[["code_commune", "scrutin", "annee", "type_scrutin", "bloc", "voix"]])

res = pd.concat(frames)
# Contrôle qualité : toute nuance / candidat non rattaché à un bloc est signalé
non_mappe = res[res.bloc.isna()]
assert non_mappe.empty, f"Nuances non rattachées : {non_mappe.head()}"

res = res.groupby(["code_commune", "scrutin", "annee", "type_scrutin", "bloc"], as_index=False).voix.sum()
part = pd.concat(particip)
res.to_csv("data_clean/resultats_bloc_commune.csv", index=False)
part.to_csv("data_clean/participation_commune.csv", index=False)
print("résultats :", res.shape, "| participation :", part.shape)
print(res.groupby("scrutin").code_commune.nunique())
