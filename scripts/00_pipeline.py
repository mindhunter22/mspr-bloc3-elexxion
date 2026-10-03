"""00 - Orchestration automatisée et sécurisée de toute la chaîne.
1. Contrôle d'intégrité : empreinte SHA-256 de chaque fichier source, comparée au manifeste précédent
   (un fichier modifié ou corrompu est signalé avant tout traitement).
2. Exécution des scripts dans l'ordre, arrêt immédiat en cas d'erreur, journal horodaté.
Usage : python scripts/00_pipeline.py [--manifeste-seulement]"""
import hashlib, json, os, subprocess, sys, time, datetime

SOURCES = "data_source"
MANIFESTE = "data_raw/manifeste_sources.json"
ETAPES = [["01_extract_xlsx_isere.py", SOURCES, "pres2022"], ["01_extract_xlsx_isere.py", SOURCES, "legi2022"],
          ["01_extract_xlsx_isere.py", SOURCES, "legi2024"], ["01b_extract_filosofi.py"], ["01c_extract_emploi.py"],
          ["02_transform.py"], ["03_features.py"], ["04_modelisation.py"], ["05_modele_final.py"], ["06_visualisations.py"],
          ["07_base_sql.py"], ["08_schemas.py"], ["09_backtest.py"], ["10_typologie.py"], ["11_requetes_nosql.py"], ["12_tableau_de_bord.py"]]

def sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()

ancien = json.load(open(MANIFESTE)) if os.path.exists(MANIFESTE) else {}
nouveau = {}
for nom in sorted(os.listdir(SOURCES)):
    p = os.path.join(SOURCES, nom)
    nouveau[nom] = {"sha256": sha256(p), "octets": os.path.getsize(os.path.realpath(p)),
                    "controle_le": datetime.datetime.now().isoformat(timespec="seconds")}
    etat = "nouveau" if nom not in ancien else ("inchangé" if ancien[nom]["sha256"] == nouveau[nom]["sha256"] else "MODIFIÉ")
    print(f"{etat:9s} {nom}  {nouveau[nom]['sha256'][:16]}…")
json.dump(nouveau, open(MANIFESTE, "w"), indent=1)
if "--manifeste-seulement" in sys.argv:
    sys.exit(0)
for etape in ETAPES:
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join("scripts", etape[0])] + etape[1:], capture_output=True, text=True)
    print(f"{'OK ' if r.returncode == 0 else 'ERREUR'} {' '.join(etape):45s} {time.time() - t:6.1f} s")
    if r.returncode != 0:
        print(r.stderr[-2000:]); sys.exit(1)
