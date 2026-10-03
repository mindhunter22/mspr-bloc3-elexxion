"""04 - Corrélations et modèles prédictifs supervisés (classification du bloc en tête)."""
import pandas as pd, numpy as np, json
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score

df = pd.read_csv("data_clean/table_modelisation.csv", dtype={"code_commune": str})
CTX = ["tx_atteintes_personnes", "tx_atteintes_biens", "tx_stupefiants", "tx_escroqueries",
       "log_population", "logements_par_hab", "evol_pop_depuis_2016", "niveau_vie_median", "taux_chomage", "participation",
       "type_PRES", "type_LEGI", "type_EURO"]
NUM = CTX[:10]  # variables de contexte numériques
LAG = ["prec_part_GAUCHE", "prec_part_CENTRE", "prec_part_DROITE", "prec_part_EXTREME_DROITE", "prec_participation"]

# ---- Corrélations (Spearman) contexte x parts de voix
cor = df[NUM + ["part_GAUCHE", "part_CENTRE", "part_DROITE", "part_EXTREME_DROITE"]].corr("spearman")
cor = cor.loc[NUM, ["part_GAUCHE", "part_CENTRE", "part_DROITE", "part_EXTREME_DROITE"]].round(2)
print(cor.to_string()); cor.to_csv("data_clean/correlations.csv")

d = df.dropna(subset=LAG).copy()
train, test = d[d.scrutin != "LEGI_2024"], d[d.scrutin == "LEGI_2024"]
y_tr, y_te = train.bloc_en_tete, test.bloc_en_tete
res = {}
# Baselines
maj = y_tr.mode()[0]
res["Baseline classe majoritaire"] = accuracy_score(y_te, [maj] * len(y_te))
res["Baseline persistance (bloc précédent)"] = accuracy_score(y_te, test.prec_bloc_en_tete)

modeles = {
    "Régression logistique": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
    "Random Forest": RandomForestClassifier(n_estimators=400, min_samples_leaf=3, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(random_state=42),
}
skf = StratifiedKFold(5, shuffle=True, random_state=42)
rows = []
for jeu, cols in [("Contexte seul", CTX), ("Contexte + scrutin précédent", CTX + LAG)]:
    for nom, m in modeles.items():
        cv = cross_val_score(m, d[cols], d.bloc_en_tete, cv=skf, scoring="accuracy")
        m.fit(train[cols], y_tr); pred = m.predict(test[cols])
        rows.append({"variables": jeu, "modèle": nom, "accuracy CV 5 plis": round(cv.mean(), 3),
                     "accuracy test 2024": round(accuracy_score(y_te, pred), 3),
                     "F1 macro test 2024": round(f1_score(y_te, pred, average="macro"), 3)})
bench = pd.DataFrame(rows); print(bench.to_string(index=False)); print(res)
bench.to_csv("data_clean/benchmark_modeles.csv", index=False)
json.dump(res, open("data_clean/baselines.json", "w"), ensure_ascii=False, indent=1)
