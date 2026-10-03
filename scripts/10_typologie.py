"""10 - Typologie des communes (apprentissage non supervisé) : combien de groupes de communes distinguer ?
K-means sur le profil socio-territorial 2024 ; le nombre de groupes est choisi par le score de silhouette."""
import sys, json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
exec(open("scripts/06_visualisations.py").read().split("# 1. Carte")[0])  # carte(), couleurs, libellés

VARS = {"log_population": "Population (log)", "logements_par_hab": "Logements par habitant",
        "niveau_vie_median": "Niveau de vie médian (€)", "taux_chomage": "Taux de chômage",
        "tx_atteintes_personnes": "Atteintes aux personnes (‰)", "tx_atteintes_biens": "Atteintes aux biens (‰)",
        "evol_pop_depuis_2016": "Évolution pop. depuis 2016"}
g = df[df.scrutin == "LEGI_2024"].set_index("code_commune")
X = g[list(VARS)].copy()
X["logements_par_hab"] = np.log(X.logements_par_hab)          # variable très asymétrique (stations de ski)
Z = StandardScaler().fit_transform(X)
scores = {k: silhouette_score(Z, KMeans(k, n_init=20, random_state=42).fit_predict(Z)) for k in range(2, 9)}
# k = 2 sépare seulement « villes » et « villages » : on retient le meilleur score à partir de 3 groupes,
# plus utile pour le métier (écart de silhouette faible avec k = 2).
k = max((k_ for k_ in scores if k_ >= 3), key=scores.get)
km = KMeans(k, n_init=20, random_state=42).fit(Z)
g["groupe"] = km.labels_
prof = g.groupby("groupe").agg(communes=("groupe", "size"), population=("insee_pop", "median"),
                               niveau_vie=("niveau_vie_median", "median"), chomage=("taux_chomage", "median"),
                               logements_hab=("logements_par_hab", "median"), atteintes_pers=("tx_atteintes_personnes", "median"),
                               part_gauche=("part_GAUCHE", "mean"), part_centre=("part_CENTRE", "mean"),
                               part_ext_droite=("part_EXTREME_DROITE", "mean"))
prof = prof.sort_values("population", ascending=False)
prof.round(3).to_csv("data_clean/typologie_communes_profils.csv")
g[["groupe"]].to_csv("data_clean/typologie_communes.csv")
print("silhouette :", {k_: round(v, 3) for k_, v in scores.items()}, "-> k =", k)
print(prof.round(3).to_string())

fig, axs = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 1.4]})
axs[0].plot(list(scores), list(scores.values()), "o-", color="#1F3A5F"); axs[0].axvline(k, ls="--", color="grey")
axs[0].set_xlabel("Nombre de groupes (k)"); axs[0].set_ylabel("Score de silhouette (plus haut = groupes mieux séparés)")
axs[0].set_title(f"Choix du nombre de groupes : k = {k}", fontsize=10)
pal = ["#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E", "#E6AB02", "#A6761D", "#666666"]
carte(axs[1], {c: pal[v] for c, v in g.groupe.items()}, "Typologie des communes de l'Isère (profil 2024)")
fig.legend(handles=[Patch(color=pal[i], label=f"Groupe {i} – {int(prof.loc[i,'communes'])} communes") for i in prof.index],
           loc="lower right", frameon=False, fontsize=9)
fig.savefig("figures/12_typologie_communes.png", dpi=150, bbox_inches="tight"); plt.close()
