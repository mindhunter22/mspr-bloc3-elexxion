"""07 - Chargement de l'entrepôt de données SQLite (modèle en étoile défini dans sql/schema.sql)."""
import sqlite3, os, sys, numpy as np, pandas as pd
sys.path.insert(0, "scripts")
from referentiel import PASSAGE_COG, BLOC_NUANCE, BLOC_PRES, BLOC_EURO2019

DB = "sql/elexxion_isere.db"
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")
con.executescript(open("sql/schema.sql", encoding="utf-8").read())

s = pd.read_csv("data_raw/ssmsi_isere.csv", dtype=str)
lib = pd.read_csv("data_raw/legi2024_t1_isere_communes.csv", dtype=str).drop_duplicates("com").set_index("com").libelle
p25 = s[s.annee == "2025"].drop_duplicates("CODGEO_2025").set_index("CODGEO_2025")
communes = pd.DataFrame({"code_commune": p25.index, "libelle": p25.index.map(lib),
                         "population_2025": p25.insee_pop.astype(int).values, "logements_2025": p25.insee_log.astype(int).values})
communes.to_sql("dim_commune", con, if_exists="append", index=False)

anciens = {"38016": "Arzay", "38121": "Commelle", "38274": "Nantoin", "38025": "Balbins", "38293": "Panissage",
           "38302": "Le Périer", "38306": "Pinsot", "38367": "Saint-Bernard", "38435": "Saint-Pancrasse"}
pd.DataFrame([(k, anciens[k], v) for k, v in PASSAGE_COG.items()], columns=["code_ancien", "libelle_ancien", "code_commune"]) \
  .to_sql("ref_passage_cog", con, if_exists="append", index=False)

pd.DataFrame([("PRES_2017", "PRES", 2017, 1, "2017-04-23"), ("LEGI_2017", "LEGI", 2017, 1, "2017-06-11"),
              ("EURO_2019", "EURO", 2019, 1, "2019-05-26"), ("PRES_2022", "PRES", 2022, 1, "2022-04-10"),
              ("LEGI_2022", "LEGI", 2022, 1, "2022-06-12"), ("LEGI_2024", "LEGI", 2024, 1, "2024-06-30")],
             columns=["id_scrutin", "type_scrutin", "annee", "tour", "date_scrutin"]).to_sql("dim_scrutin", con, if_exists="append", index=False)
pd.DataFrame([("GAUCHE", "Gauche", 1), ("CENTRE", "Centre", 2), ("DROITE", "Droite", 3),
              ("EXTREME_DROITE", "Extrême droite", 4), ("AUTRES", "Autres", 5)],
             columns=["code_bloc", "libelle", "ordre_affichage"]).to_sql("dim_bloc", con, if_exists="append", index=False)
ref = [(k, "NUANCE", v) for k, v in BLOC_NUANCE.items()] + [(k, "CANDIDAT", v) for k, v in BLOC_PRES.items()] + \
      [(k, "LISTE", v) for k, v in BLOC_EURO2019.items()]
pd.DataFrame(ref, columns=["code_nuance", "type_code", "code_bloc"]).to_sql("ref_nuance", con, if_exists="append", index=False)

fam = {"Violences physiques intrafamiliales": "Atteintes aux personnes", "Violences physiques hors cadre familial": "Atteintes aux personnes",
       "Violences sexuelles": "Atteintes aux personnes", "Vols avec armes": "Atteintes aux personnes", "Vols violents sans arme": "Atteintes aux personnes",
       "Usage de stupéfiants": "Stupéfiants", "Usage de stupéfiants (AFD)": "Stupéfiants", "Trafic de stupéfiants": "Stupéfiants",
       "Escroqueries et fraudes aux moyens de paiement": "Escroqueries"}
ind = pd.DataFrame({"indicateur": s.indicateur.unique()}); ind["famille"] = ind.indicateur.map(fam).fillna("Atteintes aux biens")
ind.to_sql("dim_indicateur_delinquance", con, if_exists="append", index=False)

part = pd.read_csv("data_clean/participation_commune.csv", dtype={"code_commune": str}).rename(columns={"scrutin": "id_scrutin"})
part.to_sql("fait_participation", con, if_exists="append", index=False)
res = pd.read_csv("data_clean/resultats_bloc_commune.csv", dtype={"code_commune": str}).rename(columns={"scrutin": "id_scrutin", "bloc": "code_bloc"})
res[["code_commune", "id_scrutin", "code_bloc", "voix"]].to_sql("fait_resultat", con, if_exists="append", index=False)

num = lambda x: pd.to_numeric(x.str.replace(",", "."), errors="coerce")
dl = pd.DataFrame({"code_commune": s.CODGEO_2025, "annee": s.annee.astype(int), "indicateur": s.indicateur,
                   "taux_pour_mille": np.where(s.est_diffuse == "diff", num(s.taux_pour_mille), num(s.complement_info_taux)),
                   "est_estime": (s.est_diffuse == "ndiff").astype(int), "population": s.insee_pop.astype(int)})
dl.to_sql("fait_delinquance", con, if_exists="append", index=False)

# Revenus et emploi (INSEE)
ctx = pd.read_csv("data_clean/contexte_commune_annee.csv", dtype={"code_commune": str})
c25 = ctx[ctx.annee == 2025].set_index("code_commune")
se = [(c, 2021, "NIVEAU_VIE_MEDIAN", r.niveau_vie_median, int(r.niveau_vie_impute)) for c, r in c25.iterrows()]
se += [(c, 2021, "TAUX_PAUVRETE", r.taux_pauvrete, 0) for c, r in c25.iterrows() if pd.notna(r.taux_pauvrete)]
em = pd.read_csv("data_raw/emploi_2010_2015_2021_isere.csv", dtype={"CODGEO": str})
for a in ("10", "15", "21"):
    se += [(r.CODGEO, 2000 + int(a), "TAUX_CHOMAGE", r[f"P{a}_CHOM1564"] / r[f"P{a}_ACT1564"], 0) for _, r in em.iterrows()]
pd.DataFrame(se, columns=["code_commune", "millesime", "indicateur", "valeur", "est_impute"]).to_sql("fait_socio_eco", con, if_exists="append", index=False)

pr = pd.read_csv("data_clean/predictions_2027_2029.csv", dtype={"code_commune": str})
rows = []
for _, r in pr.iterrows():
    for b in ["GAUCHE", "CENTRE", "DROITE", "EXTREME_DROITE"]:
        rows.append((r.code_commune, int(r.annee), r.type_scrutin, b, round(float(r[b]), 4), int(r.bloc_en_tete_predit == b), "GBR_v1"))
pd.DataFrame(rows, columns=["code_commune", "annee_cible", "type_scrutin", "code_bloc", "part_predite", "est_bloc_en_tete", "modele"]) \
  .to_sql("fait_prediction", con, if_exists="append", index=False)
con.commit()

# Contrôles d'intégrité
print(con.execute("PRAGMA foreign_key_check").fetchall() or "clés étrangères : OK")
for t in ["dim_commune", "ref_passage_cog", "dim_scrutin", "dim_bloc", "ref_nuance", "dim_indicateur_delinquance",
          "fait_participation", "fait_resultat", "fait_delinquance", "fait_socio_eco", "fait_prediction"]:
    print(f"{t:28s}", con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
print(con.execute("""SELECT id_scrutin, code_bloc, COUNT(*) FROM v_resultats WHERE rang = 1
                     GROUP BY id_scrutin, code_bloc ORDER BY id_scrutin, 3 DESC""").fetchall()[:6])
con.close()
