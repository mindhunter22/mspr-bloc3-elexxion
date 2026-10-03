-- Requêtes d'analyse exécutées automatiquement par scripts/11_requetes_nosql.py (une requête = un fichier CSV)
-- @nom: evolution_blocs_departement
SELECT r.id_scrutin, b.libelle AS bloc, SUM(r.voix) AS voix,
       ROUND(100.0 * SUM(r.voix) / SUM(SUM(r.voix)) OVER (PARTITION BY r.id_scrutin), 1) AS part_pct
FROM fait_resultat r JOIN dim_bloc b USING (code_bloc) JOIN dim_scrutin s USING (id_scrutin)
GROUP BY r.id_scrutin, b.libelle ORDER BY s.date_scrutin, b.ordre_affichage;
-- @nom: communes_ayant_change_de_bloc_2022_2024
SELECT a.libelle, a.code_bloc AS bloc_2022, b.code_bloc AS bloc_2024, c.population_2025
FROM v_resultats a JOIN v_resultats b ON a.code_commune = b.code_commune
JOIN dim_commune c ON c.code_commune = a.code_commune
WHERE a.id_scrutin = 'LEGI_2022' AND a.rang = 1 AND b.id_scrutin = 'LEGI_2024' AND b.rang = 1 AND a.code_bloc <> b.code_bloc
ORDER BY c.population_2025 DESC;
-- @nom: vote_par_tranche_niveau_de_vie_2024
WITH nv AS (SELECT code_commune, valeur, NTILE(4) OVER (ORDER BY valeur) AS quartile
            FROM fait_socio_eco WHERE indicateur = 'NIVEAU_VIE_MEDIAN')
SELECT nv.quartile, ROUND(MIN(nv.valeur)) AS niveau_vie_min, ROUND(MAX(nv.valeur)) AS niveau_vie_max,
       ROUND(AVG(CASE WHEN v.code_bloc = 'CENTRE' THEN v.part_pct END), 1) AS centre_pct,
       ROUND(AVG(CASE WHEN v.code_bloc = 'GAUCHE' THEN v.part_pct END), 1) AS gauche_pct,
       ROUND(AVG(CASE WHEN v.code_bloc = 'EXTREME_DROITE' THEN v.part_pct END), 1) AS ext_droite_pct
FROM nv JOIN v_resultats v ON v.code_commune = nv.code_commune AND v.id_scrutin = 'LEGI_2024'
GROUP BY nv.quartile ORDER BY nv.quartile;
-- @nom: part_valeurs_estimees_delinquance
SELECT annee, ROUND(100.0 * AVG(est_estime), 1) AS pct_valeurs_estimees FROM fait_delinquance GROUP BY annee ORDER BY annee;
-- @nom: projection_2027_communes_les_plus_peuplees
SELECT c.libelle, c.population_2025, p.code_bloc AS bloc_projete, ROUND(100 * p.part_predite, 1) AS part_projetee_pct
FROM fait_prediction p JOIN dim_commune c USING (code_commune)
WHERE p.annee_cible = 2027 AND p.est_bloc_en_tete = 1 ORDER BY c.population_2025 DESC LIMIT 20;
