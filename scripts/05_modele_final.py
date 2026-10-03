"""05 - Modèle final, évaluation détaillée et prédictions à 1, 2 et 3 ans.
Deux modèles supervisés complémentaires, entraînés sur 2017-2022 et testés sur les législatives 2024 :
  - un classifieur (Gradient Boosting) qui prédit directement le bloc en tête ;
  - un régresseur (Gradient Boosting, un par bloc) qui prédit la part de voix de chaque bloc,
    utilisé pour les projections pluriannuelles (on réinjecte les parts prédites comme « scrutin précédent »)."""
import numpy as np, pandas as pd, json
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, mean_absolute_error, classification_report

BLOCS = ["GAUCHE", "CENTRE", "DROITE", "EXTREME_DROITE"]
CTX = ["tx_atteintes_personnes", "tx_atteintes_biens", "tx_stupefiants", "tx_escroqueries",
       "log_population", "logements_par_hab", "evol_pop_depuis_2016", "niveau_vie_median", "taux_chomage", "participation",
       "type_PRES", "type_LEGI", "type_EURO"]
NUM = CTX[:10]  # variables de contexte numériques
LAG = [f"prec_part_{b}" for b in BLOCS] + ["prec_participation"]
X_COLS = CTX + LAG

df = pd.read_csv("data_clean/table_modelisation.csv", dtype={"code_commune": str})
d = df.dropna(subset=LAG).copy()
train, test = d[d.scrutin != "LEGI_2024"], d[d.scrutin == "LEGI_2024"]
out = {}

# ---------- 1. Corrélations intra-scrutin (on neutralise l'effet « tendance dans le temps ») ----------
intra = []
for sc, g in df.groupby("scrutin"):
    c = g[NUM + [f"part_{b}" for b in BLOCS]].corr("spearman").loc[NUM, [f"part_{b}" for b in BLOCS]]
    intra.append(c)
intra = sum(intra) / len(intra)
intra.round(2).to_csv("data_clean/correlations_intra_scrutin.csv")
print("Corrélations moyennes intra-scrutin :\n", intra.round(2))
pv = df.dropna(subset=["taux_pauvrete"])
pauv = sum(g[["taux_pauvrete"] + [f"part_{b}" for b in BLOCS]].corr("spearman").loc["taux_pauvrete", [f"part_{b}" for b in BLOCS]]
           for _, g in pv.groupby("scrutin")) / pv.scrutin.nunique()
out["correlation_taux_pauvrete_85_communes"] = pauv.round(2).to_dict()
print("Taux de pauvreté (communes où il est diffusé) :", pauv.round(2).to_dict())

# ---------- 2. Classifieur ----------
# pondération « balanced » : compense le déséquilibre des classes (peu de communes où la droite ou le centre arrivent en tête)
clf = GradientBoostingClassifier(random_state=42).fit(train[X_COLS], train.bloc_en_tete,
                                                      sample_weight=compute_sample_weight("balanced", train.bloc_en_tete))
pred = clf.predict(test[X_COLS])
labels = [b for b in BLOCS if b in set(test.bloc_en_tete) | set(pred)]
cm = pd.DataFrame(confusion_matrix(test.bloc_en_tete, pred, labels=labels), index=labels, columns=labels)
cm.to_csv("data_clean/matrice_confusion_2024.csv")
out["classif_accuracy_2024"] = accuracy_score(test.bloc_en_tete, pred)
out["classif_f1_macro_2024"] = f1_score(test.bloc_en_tete, pred, average="macro")
print(cm); print(classification_report(test.bloc_en_tete, pred, zero_division=0))
pi = permutation_importance(clf, test[X_COLS], test.bloc_en_tete, n_repeats=20, random_state=42, scoring="accuracy")
imp = pd.Series(pi.importances_mean, index=X_COLS).sort_values(ascending=False)
imp.to_csv("data_clean/importance_variables.csv", header=["baisse_accuracy"])
print(imp.round(3))

# ---------- 3. Régresseurs des parts de voix ----------
regs = {b: GradientBoostingRegressor(random_state=42).fit(train[X_COLS], train[f"part_{b}"]) for b in BLOCS}
P = pd.DataFrame({b: regs[b].predict(test[X_COLS]) for b in BLOCS}, index=test.index).clip(lower=0)
P = P.div(P.sum(axis=1), axis=0)
out["regression_MAE_points"] = {b: round(100 * mean_absolute_error(test[f"part_{b}"], P[b]), 2) for b in BLOCS}
out["regression_accuracy_bloc_2024"] = accuracy_score(test.bloc_en_tete, P.idxmax(axis=1))
# Parts départementales prédites vs réelles (pondérées par les exprimés)
w = test.exprimes
out["parts_dep_2024_reel"] = {b: round(100 * np.average(test[f"part_{b}"], weights=w), 1) for b in BLOCS}
out["parts_dep_2024_predit"] = {b: round(100 * np.average(P[b], weights=w), 1) for b in BLOCS}

# ---------- 3 bis. Réentraînement sur TOUS les scrutins (2017 à 2024) pour les projections ----------
# L'évaluation ci-dessus reste faite sur 2024 jamais vu. Pour prédire l'avenir, on utilise tout l'historique :
# le backtest (script 09) montre que plus le modèle voit d'élections, meilleur il est.
clf = GradientBoostingClassifier(random_state=42).fit(d[X_COLS], d.bloc_en_tete,
                                                      sample_weight=compute_sample_weight("balanced", d.bloc_en_tete))
regs = {b: GradientBoostingRegressor(random_state=42).fit(d[X_COLS], d[f"part_{b}"]) for b in BLOCS}
out["scrutins_apprentissage_projections"] = sorted(d.scrutin.unique().tolist())
out["lignes_apprentissage_projections"] = len(d)

# ---------- 4. Projections 2027 (présidentielle), 2028 (législatives, hypothèse), 2029 (européennes) ----------
ctx = pd.read_csv("data_clean/contexte_commune_annee.csv", dtype={"code_commune": str})
num = ["tx_atteintes_personnes", "tx_atteintes_biens", "tx_stupefiants", "tx_escroqueries", "insee_pop", "insee_log"]
def projeter(g, annee):
    """Tendance linéaire commune par commune sur 2016-2025 (moindres carrés), bornée à >= 0."""
    r = {}
    for c in num:
        a, b = np.polyfit(g.annee, g[c], 1)
        r[c] = max(a * annee + b, 0)
    return pd.Series(r)
proj = {}
for an in [2027, 2028, 2029]:
    p = ctx.groupby("code_commune").apply(projeter, annee=an, include_groups=False)
    p["log_population"] = np.log1p(p.insee_pop)
    p["logements_par_hab"] = p.insee_log / p.insee_pop.replace(0, np.nan)
    p["evol_pop_depuis_2016"] = p.insee_pop / ctx[ctx.annee == 2016].set_index("code_commune").insee_pop - 1
    p["niveau_vie_median"] = ctx[ctx.annee == 2025].set_index("code_commune").niveau_vie_median  # structurel (2021)
    p["taux_chomage"] = ctx[ctx.annee == 2025].set_index("code_commune").taux_chomage          # dernier recensement (2021)
    proj[an] = p

part_moy = df.groupby(["code_commune", df.scrutin.str[:4]]).participation.mean().unstack()
dernier = df[df.scrutin == "LEGI_2024"].set_index("code_commune")
prec = dernier[[f"part_{b}" for b in BLOCS] + ["participation"]].copy()
prec.columns = LAG
scenarios = [(2027, "PRES"), (2028, "LEGI"), (2029, "EURO")]
res = []
for an, ty in scenarios:
    X = proj[an].join(prec)
    X["participation"] = part_moy[ty]
    for t in ["PRES", "LEGI", "EURO"]:
        X[f"type_{t}"] = int(t == ty)
    X = X[X_COLS].dropna()
    Pn = pd.DataFrame({b: regs[b].predict(X) for b in BLOCS}, index=X.index).clip(lower=0)
    Pn = Pn.div(Pn.sum(axis=1), axis=0)
    Pn["bloc_en_tete_predit"] = Pn[BLOCS].idxmax(axis=1)
    Pn["bloc_en_tete_classifieur"] = clf.predict(X) if an == 2027 else None  # le classifieur n'est fiable qu'à 1 pas
    Pn["annee"], Pn["type_scrutin"] = an, ty
    res.append(Pn.reset_index())
    # le résultat prédit devient le « scrutin précédent » de l'année suivante
    prec = Pn[BLOCS].copy(); prec.columns = LAG[:4]; prec["prec_participation"] = X["participation"]
pred_all = pd.concat(res)
pred_all.to_csv("data_clean/predictions_2027_2029.csv", index=False)
inscr = dernier.exprimes
for an in [2027, 2028, 2029]:
    g = pred_all[pred_all.annee == an].set_index("code_commune")
    out[f"pred_{an}_nb_communes"] = g.bloc_en_tete_predit.value_counts().to_dict()
    out[f"pred_{an}_parts_dep"] = {b: round(100 * np.average(g[b], weights=inscr.reindex(g.index)), 1) for b in BLOCS}
out["accord_classif_regression_2027"] = float((pred_all[pred_all.annee == 2027].bloc_en_tete_predit ==
                                               pred_all[pred_all.annee == 2027].bloc_en_tete_classifieur).mean())
json.dump(out, open("data_clean/resultats_modele_final.json", "w"), ensure_ascii=False, indent=1, default=float)
print(json.dumps(out, ensure_ascii=False, indent=1, default=float))
