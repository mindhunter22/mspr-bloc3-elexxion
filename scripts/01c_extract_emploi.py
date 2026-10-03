"""01c - Extraction emploi / chômage (INSEE, recensement, base communale 2021 avec historique 2010 et 2015) pour l'Isère."""
import pandas as pd, sys
src = sys.argv[1] if len(sys.argv) > 1 else "data_source/base-cc-emploi-pop-active-2021.CSV"
cols = ["CODGEO"] + [f"P{a}_{v}1564" for a in ("10", "15", "21") for v in ("ACT", "CHOM")]
d = pd.read_csv(src, sep=";", dtype={"CODGEO": str}, usecols=lambda c: c in cols, low_memory=False)
d = d[d.CODGEO.str.startswith("38")]
d.to_csv("data_raw/emploi_2010_2015_2021_isere.csv", index=False)
print(len(d), "communes ; colonnes :", list(d.columns))
