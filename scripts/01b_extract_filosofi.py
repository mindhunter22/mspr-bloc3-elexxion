"""01b - Extraction Filosofi 2021 (INSEE, revenus et pauvreté, géographie au 01/01/2025) pour l'Isère.
Source : fichier DS_FILOSOFI_CC_data.csv (format long : une ligne = commune x mesure)."""
import pandas as pd, sys
src = sys.argv[1] if len(sys.argv) > 1 else "data_source/DS_FILOSOFI_CC_data.csv"
d = pd.read_csv(src, sep=";", dtype={"GEO": str})
d = d[(d.GEO_OBJECT == "COM") & d.GEO.str.startswith("38")]
d.to_csv("data_raw/filosofi_2021_isere.csv", index=False)
print(len(d), "lignes,", d.GEO.nunique(), "communes")
