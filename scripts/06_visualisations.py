"""06 - Visualisations (matplotlib) : cartes, corrélations, évaluation du modèle, projections."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch
from matplotlib.collections import PatchCollection

import sys; sys.path.insert(0, "scripts")
from referentiel import PASSAGE_COG as PASSAGE
BLOCS = ["GAUCHE", "CENTRE", "DROITE", "EXTREME_DROITE"]
LIB = {"GAUCHE": "Gauche", "CENTRE": "Centre", "DROITE": "Droite", "EXTREME_DROITE": "Extrême droite"}
COUL = {"GAUCHE": "#D7263D", "CENTRE": "#F2A541", "DROITE": "#2E6FB7", "EXTREME_DROITE": "#4B2E1E"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
F = "figures/"

df = pd.read_csv("data_clean/table_modelisation.csv", dtype={"code_commune": str})
pred = pd.read_csv("data_clean/predictions_2027_2029.csv", dtype={"code_commune": str})
geo = json.load(open("data_raw/contours_communes_isere.geojson"))

def carte(ax, couleurs, titre):
    patches, cols = [], []
    for f in geo["features"]:
        code = PASSAGE.get(f["properties"]["code"], f["properties"]["code"])
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            patches.append(Polygon(np.array(poly[0]), closed=True))
            cols.append(couleurs.get(code, "#DDDDDD"))
    ax.add_collection(PatchCollection(patches, facecolor=cols, edgecolor="white", linewidth=0.15))
    ax.autoscale_view(); ax.set_aspect(1 / np.cos(np.radians(45.2))); ax.axis("off"); ax.set_title(titre, fontsize=11)

def legende(fig, blocs=BLOCS):
    fig.legend(handles=[Patch(color=COUL[b], label=LIB[b]) for b in blocs], loc="lower center", ncol=4, frameon=False)

# 1. Carte du bloc en tête, législatives 2024 (réel)
fig, ax = plt.subplots(figsize=(7, 7.5))
g = df[df.scrutin == "LEGI_2024"].set_index("code_commune").bloc_en_tete
carte(ax, {k: COUL[v] for k, v in g.items()}, "Bloc arrivé en tête par commune – législatives 2024, 1er tour")
legende(fig); fig.savefig(F + "01_carte_legislatives_2024.png", dpi=160, bbox_inches="tight"); plt.close()

# 2. Les deux variables de contexte les plus corrélées (législatives 2024)
g = df[df.scrutin == "LEGI_2024"]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
axs[0].scatter(g.logements_par_hab, 100 * g.part_GAUCHE, s=10, alpha=.6, color=COUL["GAUCHE"])
axs[0].set_xscale("log"); axs[0].set_xlabel("Logements par habitant (échelle log)"); axs[0].set_ylabel("Part de la gauche (% des exprimés)")
axs[0].set_title("Plus de logements par habitant → plus de vote à gauche\n(ρ intra-scrutin = +0,44)", fontsize=10)
axs[1].scatter(100 * g.participation, 100 * g.part_EXTREME_DROITE, s=10, alpha=.6, color=COUL["EXTREME_DROITE"])
axs[1].set_xlabel("Participation (% des inscrits)"); axs[1].set_ylabel("Part de l'extrême droite (% des exprimés)")
axs[1].set_title("Participation plus forte → vote d'extrême droite plus faible\n(ρ intra-scrutin = −0,35)", fontsize=10)
fig.suptitle("Législatives 2024 – une commune = un point", fontsize=11)
fig.tight_layout(); fig.savefig(F + "02_nuages_correlations.png", dpi=160, bbox_inches="tight"); plt.close()

# 3. Corrélations : toutes années confondues vs à scrutin identique
pooled = pd.read_csv("data_clean/correlations.csv", index_col=0)
intra = pd.read_csv("data_clean/correlations_intra_scrutin.csv", index_col=0)
lignes = {"tx_atteintes_personnes": "Atteintes aux personnes (‰)", "tx_atteintes_biens": "Atteintes aux biens (‰)",
          "tx_stupefiants": "Stupéfiants (‰)", "tx_escroqueries": "Escroqueries (‰)", "log_population": "Population (log)",
          "logements_par_hab": "Logements par habitant", "evol_pop_depuis_2016": "Évolution pop. depuis 2016", "niveau_vie_median": "Niveau de vie médian (€)", "taux_chomage": "Taux de chômage 15-64 ans",
          "participation": "Participation"}
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
for ax, m, t in [(axs[0], pooled, "Tous scrutins mélangés"), (axs[1], intra, "Moyenne à scrutin identique (retenue)")]:
    im = ax.imshow(m.values, cmap="RdBu_r", vmin=-.5, vmax=.5)
    ax.set_xticks(range(4)); ax.set_xticklabels([LIB[b] for b in BLOCS], rotation=20)
    ax.set_yticks(range(len(m))); ax.set_yticklabels([lignes[i] for i in m.index]); ax.set_title(t, fontsize=10)
    for i in range(m.shape[0]):
        for j in range(4):
            ax.text(j, i, f"{m.values[i, j]:+.2f}".replace(".", ","), ha="center", va="center", fontsize=8,
                    color="white" if abs(m.values[i, j]) > .3 else "black")
fig.colorbar(im, ax=axs, shrink=.8, label="Corrélation de Spearman")
fig.suptitle("Corrélation entre le contexte communal et la part de voix de chaque bloc", fontsize=11)
fig.savefig(F + "03_correlations.png", dpi=160, bbox_inches="tight"); plt.close()

# 4. Comparaison des modèles (test sur les législatives 2024)
bench = pd.read_csv("data_clean/benchmark_modeles.csv")
base = json.load(open("data_clean/baselines.json")); fin = json.load(open("data_clean/resultats_modele_final.json"))
rows = [("Classe majoritaire", base["Baseline classe majoritaire"], "#BBBBBB"),
        ("Persistance (bloc précédent)", base["Baseline persistance (bloc précédent)"], "#BBBBBB")]
for _, r in bench.iterrows():
    rows.append((f"{r['modèle']} – {r['variables'].lower()}", r["accuracy test 2024"], "#9DB4CF" if r["variables"] == "Contexte seul" else "#4F7CAC"))
rows.append(("Gradient Boosting pondéré – modèle retenu", fin["classif_accuracy_2024"], "#1F3A5F"))
fig, ax = plt.subplots(figsize=(8.5, 4.6))
y = np.arange(len(rows))[::-1]
ax.barh(y, [100 * r[1] for r in rows], color=[r[2] for r in rows])
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=9)
for yi, r in zip(y, rows):
    ax.text(100 * r[1] + 1, yi, f"{100 * r[1]:.0f} %", va="center", fontsize=9)
ax.set_xlim(0, 100); ax.set_xlabel("Accuracy sur les législatives 2024 (%)")
ax.set_title("Accuracy des modèles testés (entraînement 2017-2022, test 2024)", fontsize=11)
fig.tight_layout(); fig.savefig(F + "04_comparaison_modeles.png", dpi=160, bbox_inches="tight"); plt.close()

# 5. Matrice de confusion
cm = pd.read_csv("data_clean/matrice_confusion_2024.csv", index_col=0)
fig, ax = plt.subplots(figsize=(5.8, 4.8))
ax.imshow(cm.values, cmap="Blues")
ax.set_xticks(range(len(cm))); ax.set_xticklabels([LIB[c] for c in cm.columns], rotation=20)
ax.set_yticks(range(len(cm))); ax.set_yticklabels([LIB[c] for c in cm.index])
for i in range(len(cm)):
    for j in range(len(cm)):
        ax.text(j, i, cm.values[i, j], ha="center", va="center", color="white" if cm.values[i, j] > 100 else "black")
ax.set_xlabel("Bloc prédit"); ax.set_ylabel("Bloc réel")
ax.set_title("Matrice de confusion – législatives 2024 (512 communes)", fontsize=10)
fig.tight_layout(); fig.savefig(F + "05_matrice_confusion.png", dpi=160, bbox_inches="tight"); plt.close()

# 6. Importance des variables (permutation)
imp = pd.read_csv("data_clean/importance_variables.csv", index_col=0).iloc[:, 0]
noms = {**lignes, "prec_part_GAUCHE": "Part gauche au scrutin précédent", "prec_part_CENTRE": "Part centre au scrutin précédent",
        "prec_part_DROITE": "Part droite au scrutin précédent", "prec_part_EXTREME_DROITE": "Part ext. droite au scrutin précédent",
        "prec_participation": "Participation au scrutin précédent", "type_PRES": "Type : présidentielle",
        "type_LEGI": "Type : législatives", "type_EURO": "Type : européennes"}
imp = imp.head(8)[::-1]
fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.barh([noms[i] for i in imp.index], 100 * imp.values, color=["#1F3A5F" if v > 0.01 else "#9DB4CF" for v in imp.values])
ax.axvline(0, color="grey", lw=.8); ax.set_xlabel("Perte d'accuracy si la variable est brouillée (points)")
ax.set_title("Variables les plus utiles au modèle (importance par permutation)", fontsize=10)
fig.tight_layout(); fig.savefig(F + "06_importance_variables.png", dpi=160, bbox_inches="tight"); plt.close()

# 7. Évolution observée et projection départementale
w = df[df.scrutin == "LEGI_2024"].set_index("code_commune").exprimes
obs = df.groupby("scrutin").apply(lambda g: pd.Series({b: np.average(g[f"part_{b}"], weights=g.exprimes) for b in BLOCS}), include_groups=False)
ordre = ["PRES_2017", "LEGI_2017", "EURO_2019", "PRES_2022", "LEGI_2022", "LEGI_2024"]
obs = obs.loc[ordre]
xo = list(range(6))                      # scrutins observés, régulièrement espacés
lab_o = ["Prés. 2017", "Légis. 2017", "Euro. 2019", "Prés. 2022", "Légis. 2022", "Légis. 2024"]
pr = pred.groupby("annee").apply(lambda g: pd.Series({b: np.average(g[b], weights=w.reindex(g.code_commune)) for b in BLOCS}), include_groups=False)
xp = [7, 8, 9]
mae = fin["regression_MAE_points"]
decal = {"GAUCHE": -.15, "CENTRE": -.05, "DROITE": .05, "EXTREME_DROITE": .15}
fig, ax = plt.subplots(figsize=(10, 4.8))
for b in BLOCS:
    ax.plot(xo, 100 * obs[b], "o-", color=COUL[b], lw=2, label=LIB[b])
    ax.plot([xo[-1]] + xp, [100 * obs[b].iloc[-1]] + list(100 * pr[b]), "--", color=COUL[b], lw=1.6)
    ax.errorbar([x + decal[b] for x in xp], 100 * pr[b], yerr=mae[b], fmt="s", color=COUL[b], capsize=3, ms=5, lw=1.2)
ax.axvspan(6.3, 9.6, color="#F2F2F2", zorder=0)
ax.text(6.4, 1.5, "Projection (barres = ± erreur moyenne mesurée en 2024)", fontsize=8.5, color="#555")
ax.set_xticks(xo + xp); ax.set_xticklabels(lab_o + ["Prés. 2027", "Légis. 2028\n(hypothèse)", "Euro. 2029"], fontsize=8.5)
ax.set_ylabel("Part des suffrages exprimés en Isère (%)"); ax.set_ylim(0, 52); ax.set_xlim(-.4, 9.6)
ax.legend(frameon=False, ncol=4, loc="upper left")
ax.set_title("Isère : parts de voix par bloc, observées (2017-2024) et projetées (2027-2029)", fontsize=11)
fig.tight_layout(); fig.savefig(F + "07_evolution_et_projections.png", dpi=160, bbox_inches="tight"); plt.close()

# 8. Cartes des projections
fig, axs = plt.subplots(1, 3, figsize=(16, 6.2))
for ax, (an, t) in zip(axs, [(2027, "Présidentielle 2027 (à 1 an)"), (2028, "Législatives 2028 – hypothèse (à 2 ans)"), (2029, "Européennes 2029 (à 3 ans)")]):
    g = pred[pred.annee == an].set_index("code_commune").bloc_en_tete_predit
    n = g.value_counts()
    carte(ax, {k: COUL[v] for k, v in g.items()},
          t + f"\nGauche {n.get('GAUCHE', 0)} · Centre {n.get('CENTRE', 0)} · Droite {n.get('DROITE', 0)}\nExtrême droite {n.get('EXTREME_DROITE', 0)} communes")
legende(fig); fig.suptitle("Bloc en tête projeté par commune", fontsize=12)
fig.savefig(F + "08_cartes_projections.png", dpi=150, bbox_inches="tight"); plt.close()
print("ok")
