"""11 - Exploitation automatisée de l'entrepôt :
(a) exécute les requêtes de sql/requetes_analyse.sql et exporte chaque résultat en CSV ;
(b) produit une version NoSQL orientée document (un document JSON par commune), prête pour MongoDB."""
import sqlite3, json, re, pandas as pd
con = sqlite3.connect("file:sql/elexxion_isere.db?mode=ro", uri=True)   # lecture seule
sql = open("sql/requetes_analyse.sql", encoding="utf-8").read()
for nom, requete in re.findall(r"-- @nom: (\w+)\n(.*?;)", sql, flags=re.S):
    r = pd.read_sql(requete, con)
    r.to_csv(f"resultats_requetes/{nom}.csv", index=False)
    print(f"{nom}: {len(r)} lignes"); print(r.head(4).to_string(index=False))

# ----- Modèle document (NoSQL) : une commune = un document auto-suffisant -----
res = pd.read_sql("SELECT code_commune, id_scrutin, code_bloc, part_pct, participation_pct FROM v_resultats", con)
se = pd.read_sql("SELECT * FROM fait_socio_eco", con)
pr = pd.read_sql("SELECT * FROM fait_prediction", con)
com = pd.read_sql("SELECT * FROM dim_commune", con)
typo = pd.read_csv("data_clean/typologie_communes.csv", dtype={"code_commune": str}).set_index("code_commune").groupe
docs = []
for _, c in com.iterrows():
    cc = c.code_commune
    r = res[res.code_commune == cc]
    docs.append({
        "_id": cc, "libelle": c.libelle, "population_2025": int(c.population_2025), "groupe_typologie": int(typo.get(cc, -1)),
        "socio_eco": {f"{x.indicateur.lower()}_{x.millesime}": round(x.valeur, 4) for x in se[se.code_commune == cc].itertuples()},
        "resultats": {s: {"participation_pct": g.participation_pct.iloc[0],
                          "parts_pct": dict(zip(g.code_bloc, g.part_pct))} for s, g in r.groupby("id_scrutin")},
        "projections": {str(a): {"bloc_en_tete": g[g.est_bloc_en_tete == 1].code_bloc.iloc[0],
                                 "parts": dict(zip(g.code_bloc, g.part_predite.round(4)))} for a, g in pr[pr.code_commune == cc].groupby("annee_cible")},
    })
json.dump(docs, open("data_clean/nosql_communes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("NoSQL :", len(docs), "documents ; exemple :", json.dumps(docs[0], ensure_ascii=False)[:400])
