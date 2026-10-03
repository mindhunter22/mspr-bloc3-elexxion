"""08 - Schémas du dossier : flux de données (ETL) et modèle en étoile de l'entrepôt."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

def boite(ax, x, y, w, h, titre, lignes, coul):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=coul, ec="#333", lw=1))
    ax.text(x + w / 2, y + h - 0.18, titre, ha="center", va="top", fontsize=9.5, weight="bold")
    for i, l in enumerate(lignes):
        ax.text(x + 0.1, y + h - 0.55 - i * 0.3, l, ha="left", va="top", fontsize=7.8, family="DejaVu Sans Mono" if "│" in l or l.startswith(("PK", "FK", " ")) else "DejaVu Sans")

def fleche(ax, x1, y1, x2, y2, txt=""):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.3))
    if txt:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, txt, ha="center", fontsize=7.5, color="#444")

# ---------- Flux de données ----------
fig, ax = plt.subplots(figsize=(14, 5.2)); ax.set_xlim(0, 14); ax.set_ylim(0, 5.2); ax.axis("off")
S, T, L, U = "#E8EEF6", "#FFF3D6", "#E3F1E3", "#F6E3E8"
boite(ax, 0.1, 2.9, 2.6, 2.1, "SOURCES (data.gouv.fr)", ["Résultats électoraux", "Min. Intérieur : 6 scrutins", "Délinquance : SSMSI 2016-2025", "Revenus : INSEE Filosofi 2021", "Emploi : INSEE recensement"], S)
boite(ax, 0.1, 0.4, 2.6, 1.9, "RÉFÉRENTIEL", ["referentiel.py", "• passage COG 2017→2025", "• nuance → bloc politique", "  (61 correspondances)"], S)
boite(ax, 3.3, 2.9, 2.4, 2.1, "01 EXTRACTION", ["Lecture xlsx / csv", "Filtre Isère (38)", "Format long :", "commune × candidat"], T)
boite(ax, 6.2, 2.9, 2.5, 2.1, "02-03 TRANSFORMATION", ["Rattachement aux blocs", "Harmonisation COG 2025", "Agrégation par commune", "Contrôles qualité", "Taux ‰, variables décalées"], T)
boite(ax, 6.2, 0.4, 2.5, 1.9, "07 CHARGEMENT", ["Entrepôt SQLite", "modèle en étoile", "10 tables + 1 vue", "contrôle des clés"], L)
boite(ax, 9.3, 2.9, 2.2, 2.1, "04-05 MODÈLES", ["Corrélations", "3 algorithmes comparés", "Test sur 2024", "Prédictions 2027-2029"], L)
boite(ax, 12.0, 2.9, 1.9, 2.1, "RESTITUTION", ["06 Figures", "Cartes", "Dossier", "Tableau de bord"], U)
boite(ax, 9.3, 0.4, 4.6, 1.9, "UTILISATEURS ELEXXION", ["Dirigeant : fiabilité, investissement", "Expert politique : facteurs du vote", "Business developer : communes cibles"], U)
fleche(ax, 2.7, 3.95, 3.3, 3.95, "brut")
fleche(ax, 5.7, 3.95, 6.2, 3.95)
fleche(ax, 1.4, 2.3, 6.2, 3.3, "")
fleche(ax, 7.45, 2.9, 7.45, 2.3, "")
fleche(ax, 8.7, 3.95, 9.3, 3.95)
fleche(ax, 11.5, 3.95, 12.0, 3.95)
fleche(ax, 12.95, 2.9, 12.95, 2.3)
fleche(ax, 8.7, 1.35, 9.3, 1.35, "SQL")
ax.set_title("Flux de données du POC – de la source à la décision", fontsize=12, weight="bold")
fig.savefig("figures/09_flux_donnees.png", dpi=160, bbox_inches="tight"); plt.close()

# ---------- Modèle en étoile ----------
fig, ax = plt.subplots(figsize=(13, 9.6)); ax.set_xlim(0, 13); ax.set_ylim(0, 9.6); ax.axis("off")
D, F, R = "#E8EEF6", "#FFF3D6", "#E3F1E3"
boite(ax, 4.9, 5.2, 3.2, 2.0, "dim_commune", ["PK code_commune", "   libelle", "   population_2025", "   logements_2025"], D)
boite(ax, 0.2, 5.2, 3.3, 2.0, "ref_passage_cog", ["PK code_ancien", "   libelle_ancien", "FK code_commune"], R)
boite(ax, 9.5, 5.2, 3.3, 2.0, "dim_scrutin", ["PK id_scrutin", "   type_scrutin", "   annee, tour", "   date_scrutin"], D)
boite(ax, 0.2, 2.6, 3.3, 2.1, "fait_delinquance", ["PK code_commune (FK)", "PK annee", "PK indicateur (FK)", "   taux_pour_mille", "   est_estime, population"], F)
boite(ax, 4.9, 2.6, 3.2, 2.1, "fait_resultat", ["PK code_commune (FK)", "PK id_scrutin (FK)", "PK code_bloc (FK)", "   voix"], F)
boite(ax, 9.5, 2.6, 3.3, 2.1, "fait_participation", ["PK code_commune (FK)", "PK id_scrutin (FK)", "   inscrits, votants", "   exprimes"], F)
boite(ax, 4.9, 7.6, 3.2, 1.6, "fait_socio_eco", ["PK code_commune (FK)", "PK millesime, indicateur", "   valeur, est_impute"], F)
boite(ax, 0.2, 0.1, 3.3, 1.9, "dim_indicateur_delinquance", ["PK indicateur", "   famille"], D)
boite(ax, 4.9, 0.1, 3.2, 1.9, "dim_bloc", ["PK code_bloc", "   libelle", "   ordre_affichage"], D)
boite(ax, 9.5, 0.1, 3.3, 1.9, "fait_prediction", ["PK code_commune (FK)", "PK annee_cible, code_bloc (FK)", "   part_predite, est_bloc_en_tete", "   type_scrutin, modele"], F)
boite(ax, 8.15, 0.1, 1.25, 1.9, "ref_nuance", ["PK code", "PK type", "FK bloc"], R)
for (x1, y1, x2, y2) in [(3.5, 6.2, 4.9, 6.2), (6.5, 4.7, 6.5, 5.2), (8.1, 4.2, 9.5, 5.6), (3.5, 4.2, 4.9, 5.6),
                         (6.5, 2.6, 6.5, 2.0), (1.85, 2.6, 1.85, 2.0), (11.15, 4.7, 11.15, 5.2), (8.1, 3.6, 9.5, 3.6),
                         (8.1, 6.2, 9.5, 6.2), (6.5, 7.6, 6.5, 7.2), (8.1, 5.4, 9.8, 2.0), (8.2, 1.0, 8.1, 1.0)]:
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-", color="#777", lw=1))
ax.text(6.5, 9.5, "Entrepôt de données Elexxion – modèle en étoile (bleu : dimensions · jaune : faits · vert : référentiels)",
        ha="center", fontsize=11, weight="bold")
fig.savefig("figures/10_modele_etoile.png", dpi=160, bbox_inches="tight"); plt.close()
print("ok")
