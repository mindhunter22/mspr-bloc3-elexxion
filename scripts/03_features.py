"""03 - Construction du jeu de modélisation : une ligne = (commune, scrutin).
Variables : contexte socio-territorial (SSMSI / INSEE), participation, résultats du scrutin précédent.
Cible : bloc politique arrivé en tête au 1er tour."""
import numpy as np, pandas as pd

ORDRE = ["PRES_2017", "LEGI_2017", "EURO_2019", "PRES_2022", "LEGI_2022", "LEGI_2024"]
BLOCS = ["GAUCHE", "CENTRE", "DROITE", "EXTREME_DROITE"]
FAMILLES = {
    "atteintes_personnes": ["Violences physiques intrafamiliales", "Violences physiques hors cadre familial",
                            "Violences sexuelles", "Vols avec armes", "Vols violents sans arme"],
    "atteintes_biens": ["Vols sans violence contre des personnes", "Cambriolages de logement", "Vols de véhicule",
                        "Vols dans les véhicules", "Vols d'accessoires sur véhicules",
                        "Destructions et dégradations volontaires"],
    "stupefiants": ["Usage de stupéfiants", "Usage de stupéfiants (AFD)", "Trafic de stupéfiants"],
    "escroqueries": ["Escroqueries et fraudes aux moyens de paiement"],
}

# ---------- Délinquance (SSMSI) : taux pour 1 000 habitants par famille ----------
s = pd.read_csv("data_raw/ssmsi_isere.csv", dtype=str)
num = lambda x: pd.to_numeric(x.str.replace(",", "."), errors="coerce")
s["taux"] = np.where(s.est_diffuse == "diff", num(s.taux_pour_mille), num(s.complement_info_taux))
s["estime"] = (s.est_diffuse == "ndiff").astype(int)          # traçabilité de l'imputation
s["annee"] = s.annee.astype(int)
fam = {i: f for f, lst in FAMILLES.items() for i in lst}
s["famille"] = s.indicateur.map(fam)
delinq = s.pivot_table(index=["CODGEO_2025", "annee"], columns="famille", values="taux", aggfunc="sum").add_prefix("tx_")
delinq["part_valeurs_estimees"] = s.groupby(["CODGEO_2025", "annee"]).estime.mean()
pop = s.drop_duplicates(["CODGEO_2025", "annee"]).set_index(["CODGEO_2025", "annee"])[["insee_pop", "insee_log"]].apply(pd.to_numeric)
ctx = delinq.join(pop).reset_index().rename(columns={"CODGEO_2025": "code_commune"})
ctx["log_population"] = np.log1p(ctx.insee_pop)
ctx["logements_par_hab"] = ctx.insee_log / ctx.insee_pop
p2016 = ctx[ctx.annee == 2016].set_index("code_commune").insee_pop
ctx["evol_pop_depuis_2016"] = ctx.insee_pop / ctx.code_commune.map(p2016) - 1
# ---------- Revenus et pauvreté (INSEE Filosofi 2021) ----------
# Donnée structurelle d'un seul millésime (le dernier publié) : on l'applique à tous les scrutins.
fi = pd.read_csv("data_raw/filosofi_2021_isere.csv", dtype={"GEO": str})
fi = fi.pivot_table(index="GEO", columns="FILOSOFI_MEASURE", values="OBS_VALUE")
revenus = pd.DataFrame({"niveau_vie_median": fi["MED_SL"], "taux_pauvrete": fi["PR_MD60"]})
revenus = revenus.reindex(ctx.code_commune.unique())
# Secret statistique : le niveau de vie médian manque pour les très petites communes (< 50 ménages).
# Imputation par la médiane des communes de taille comparable (quintile de population 2021) + indicateur.
pop21 = ctx[ctx.annee == 2021].set_index("code_commune").insee_pop.reindex(revenus.index)
revenus["niveau_vie_impute"] = revenus.niveau_vie_median.isna().astype(int)
classe = pd.qcut(pop21, 5, labels=False)
revenus["niveau_vie_median"] = revenus.niveau_vie_median.fillna(revenus.groupby(classe).niveau_vie_median.transform("median"))
print("Niveau de vie imputé :", revenus.niveau_vie_impute.sum(), "communes ; taux de pauvreté diffusé :",
      revenus.taux_pauvrete.notna().sum(), "communes")
ctx = ctx.merge(revenus.rename_axis("code_commune").reset_index(), on="code_commune", how="left")

# ---------- Emploi (INSEE, recensement 2010, 2015, 2021) ----------
# Taux de chômage des 15-64 ans (au sens du recensement). Interpolation linéaire entre millésimes ;
# après 2021, dernière valeur connue (pas d'extrapolation).
em = pd.read_csv("data_raw/emploi_2010_2015_2021_isere.csv", dtype={"CODGEO": str}).set_index("CODGEO")
tx = pd.DataFrame({a: em[f"P{str(a)[2:]}_CHOM1564"] / em[f"P{str(a)[2:]}_ACT1564"] for a in (2010, 2015, 2021)})
ctx["taux_chomage"] = [np.interp(an, [2010, 2015, 2021], tx.loc[c].values) for c, an in zip(ctx.code_commune, ctx.annee)]
ctx.to_csv("data_clean/contexte_commune_annee.csv", index=False)

# ---------- Résultats : parts de voix par bloc + participation ----------
r = pd.read_csv("data_clean/resultats_bloc_commune.csv", dtype={"code_commune": str})
p = pd.read_csv("data_clean/participation_commune.csv", dtype={"code_commune": str})
parts = r.pivot_table(index=["code_commune", "scrutin"], columns="bloc", values="voix", aggfunc="sum").fillna(0)
parts = parts.div(parts.sum(axis=1), axis=0)[BLOCS].add_prefix("part_").reset_index()
parts = parts.merge(p, on=["code_commune", "scrutin"])
# Contrôle qualité : scrutin sans suffrage exprimé (ex. Lieudieu, présidentielle 2022 : tous les votes annulés) -> exclu
anomalies = parts[parts.exprimes == 0]
print("Anomalies exclues :", anomalies[["code_commune", "scrutin", "votants", "exprimes"]].to_dict("records"))
parts = parts[parts.exprimes > 0].copy()
parts["participation"] = parts.votants / parts.inscrits
parts["bloc_en_tete"] = parts[[f"part_{b}" for b in BLOCS]].idxmax(axis=1).str.replace("part_", "")
parts["rang"] = parts.scrutin.map({s: i for i, s in enumerate(ORDRE)})
parts["annee"] = parts.scrutin.str[-4:].astype(int)
parts["type_scrutin"] = parts.scrutin.str[:4]
parts = parts.sort_values(["code_commune", "rang"])

# variables décalées : résultat du scrutin précédent (même commune)
lag_cols = [f"part_{b}" for b in BLOCS] + ["participation"]
for c in lag_cols:
    parts[f"prec_{c}"] = parts.groupby("code_commune")[c].shift(1)
parts["prec_bloc_en_tete"] = parts.groupby("code_commune").bloc_en_tete.shift(1)

df = parts.merge(ctx, on=["code_commune", "annee"], how="left")
df = pd.get_dummies(df, columns=["type_scrutin"], prefix="type", dtype=int)
df.to_csv("data_clean/table_modelisation.csv", index=False)
print(df.shape); print(df.isna().sum()[df.isna().sum() > 0])
