"""09 - Validation sur deux élections différentes (backtest).
Test A : présidentielle 2022, prédite comme si l'on était début 2022 (apprentissage sur législatives 2017 et européennes 2019).
Test B : législatives 2024, prédites à partir de 2017-2022 (test principal, voir 05).
Pour chaque test : même modèle (Gradient Boosting pondéré), mêmes variables, mêmes références naïves."""
import json, sys, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import accuracy_score, f1_score
sys.path.insert(0, "scripts")
exec(open("scripts/06_visualisations.py").read().split("# 1. Carte")[0])  # réutilise carte(), couleurs et libellés

BLOCS = ["GAUCHE", "CENTRE", "DROITE", "EXTREME_DROITE"]
CTX = ["tx_atteintes_personnes", "tx_atteintes_biens", "tx_stupefiants", "tx_escroqueries", "log_population",
       "logements_par_hab", "evol_pop_depuis_2016", "niveau_vie_median", "taux_chomage", "participation",
       "type_PRES", "type_LEGI", "type_EURO"]
LAG = [f"prec_part_{b}" for b in BLOCS] + ["prec_participation"]
df = pd.read_csv("data_clean/table_modelisation.csv", dtype={"code_commune": str})
d = df.dropna(subset=LAG)
geo = json.load(open("data_raw/contours_communes_isere.geojson"))
meme_type = {"PRES_2022": "PRES_2017", "LEGI_2024": "LEGI_2022"}
tests = [("A – Présidentielle 2022", "PRES_2022", ["LEGI_2017", "EURO_2019"]),
         ("B – Législatives 2024", "LEGI_2024", ["LEGI_2017", "EURO_2019", "PRES_2022", "LEGI_2022"])]
rows, preds = [], {}
for nom, test, trains in tests:
    tr, te = d[d.scrutin.isin(trains)], d[d.scrutin == test]
    m = GradientBoostingClassifier(random_state=42).fit(tr[CTX + LAG], tr.bloc_en_tete,
                                                        sample_weight=compute_sample_weight("balanced", tr.bloc_en_tete))
    p = m.predict(te[CTX + LAG]); preds[test] = pd.Series(p, index=te.code_commune)
    same = df[df.scrutin == meme_type[test]].set_index("code_commune").bloc_en_tete
    rows.append({"test": nom, "scrutins d'apprentissage": len(trains), "lignes d'apprentissage": len(tr),
                 "accuracy modèle": accuracy_score(te.bloc_en_tete, p), "F1 macro": f1_score(te.bloc_en_tete, p, average="macro"),
                 "persistance scrutin précédent": accuracy_score(te.bloc_en_tete, te.prec_bloc_en_tete),
                 "persistance même type d'élection": accuracy_score(te.bloc_en_tete, te.code_commune.map(same)),
                 "classe majoritaire": (te.bloc_en_tete == tr.bloc_en_tete.mode()[0]).mean(),
                 "communes par bloc (réel)": te.bloc_en_tete.value_counts().to_dict(),
                 "communes par bloc (prédit)": pd.Series(p).value_counts().to_dict()})
res = pd.DataFrame(rows); res.to_csv("data_clean/backtest_deux_elections.csv", index=False)
print(res.drop(columns=["communes par bloc (réel)", "communes par bloc (prédit)"]).round(3).to_string(index=False))
print(res[["test", "communes par bloc (réel)", "communes par bloc (prédit)"]].to_string(index=False))

# Figure : présidentielles 2017 et 2022 réelles, 2022 prédite
fig, axs = plt.subplots(1, 3, figsize=(16, 6.2))
reel = lambda s: df[df.scrutin == s].set_index("code_commune").bloc_en_tete
for ax, (serie, titre) in zip(axs, [(reel("PRES_2017"), "Présidentielle 2017 – réel"),
                                    (reel("PRES_2022"), "Présidentielle 2022 – réel"),
                                    (preds["PRES_2022"], "Présidentielle 2022 – prédit avec les données 2017-2019")]):
    n = serie.value_counts()
    carte(ax, {k: COUL[v] for k, v in serie.items()},
          titre + f"\nGauche {n.get('GAUCHE', 0)} · Centre {n.get('CENTRE', 0)} · Droite {n.get('DROITE', 0)} · Ext. droite {n.get('EXTREME_DROITE', 0)}")
legende(fig); fig.suptitle("Bloc en tête par commune : deux présidentielles comparées et test de prédiction", fontsize=12)
fig.savefig("figures/11_backtest_presidentielles.png", dpi=150, bbox_inches="tight"); plt.close()
print("ok")
