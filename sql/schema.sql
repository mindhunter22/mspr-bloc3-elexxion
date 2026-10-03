-- Entrepôt de données du POC Elexxion (SQLite) – modèle en étoile
-- Dimensions et référentiels
CREATE TABLE dim_commune (
    code_commune      TEXT PRIMARY KEY,          -- code INSEE, COG 2025
    libelle           TEXT NOT NULL,
    population_2025   INTEGER,
    logements_2025    INTEGER
);
CREATE TABLE ref_passage_cog (                   -- communes fusionnées depuis 2017
    code_ancien       TEXT PRIMARY KEY,
    libelle_ancien    TEXT NOT NULL,
    code_commune      TEXT NOT NULL REFERENCES dim_commune(code_commune)
);
CREATE TABLE dim_scrutin (
    id_scrutin        TEXT PRIMARY KEY,          -- ex. LEGI_2024
    type_scrutin      TEXT NOT NULL CHECK (type_scrutin IN ('PRES','LEGI','EURO')),
    annee             INTEGER NOT NULL,
    tour              INTEGER NOT NULL DEFAULT 1,
    date_scrutin      TEXT NOT NULL
);
CREATE TABLE dim_bloc (
    code_bloc         TEXT PRIMARY KEY,
    libelle           TEXT NOT NULL,
    ordre_affichage   INTEGER NOT NULL
);
CREATE TABLE ref_nuance (                        -- rattachement nuance / candidat / liste -> bloc
    code_nuance       TEXT NOT NULL,
    type_code         TEXT NOT NULL CHECK (type_code IN ('NUANCE','CANDIDAT','LISTE')),
    code_bloc         TEXT NOT NULL REFERENCES dim_bloc(code_bloc),
    PRIMARY KEY (code_nuance, type_code)
);
CREATE TABLE dim_indicateur_delinquance (
    indicateur        TEXT PRIMARY KEY,
    famille           TEXT NOT NULL
);
-- Faits
CREATE TABLE fait_participation (
    code_commune      TEXT NOT NULL REFERENCES dim_commune(code_commune),
    id_scrutin        TEXT NOT NULL REFERENCES dim_scrutin(id_scrutin),
    inscrits          INTEGER NOT NULL CHECK (inscrits >= votants),
    votants           INTEGER NOT NULL CHECK (votants >= exprimes),
    exprimes          INTEGER NOT NULL CHECK (exprimes >= 0),
    PRIMARY KEY (code_commune, id_scrutin)
);
CREATE TABLE fait_resultat (
    code_commune      TEXT NOT NULL REFERENCES dim_commune(code_commune),
    id_scrutin        TEXT NOT NULL REFERENCES dim_scrutin(id_scrutin),
    code_bloc         TEXT NOT NULL REFERENCES dim_bloc(code_bloc),
    voix              INTEGER NOT NULL CHECK (voix >= 0),
    PRIMARY KEY (code_commune, id_scrutin, code_bloc)
);
CREATE TABLE fait_delinquance (
    code_commune      TEXT NOT NULL REFERENCES dim_commune(code_commune),
    annee             INTEGER NOT NULL,
    indicateur        TEXT NOT NULL REFERENCES dim_indicateur_delinquance(indicateur),
    taux_pour_mille   REAL,
    est_estime        INTEGER NOT NULL CHECK (est_estime IN (0,1)),   -- 1 = valeur non diffusée, estimation SSMSI
    population        INTEGER,
    PRIMARY KEY (code_commune, annee, indicateur)
);
CREATE TABLE fait_socio_eco (                  -- revenus (Filosofi 2021) et emploi (recensement 2010, 2015, 2021)
    code_commune      TEXT NOT NULL REFERENCES dim_commune(code_commune),
    millesime         INTEGER NOT NULL,
    indicateur        TEXT NOT NULL CHECK (indicateur IN ('NIVEAU_VIE_MEDIAN','TAUX_PAUVRETE','TAUX_CHOMAGE')),
    valeur            REAL NOT NULL,
    est_impute        INTEGER NOT NULL CHECK (est_impute IN (0,1)),
    PRIMARY KEY (code_commune, millesime, indicateur)
);
CREATE TABLE fait_prediction (
    code_commune      TEXT NOT NULL REFERENCES dim_commune(code_commune),
    annee_cible       INTEGER NOT NULL,
    type_scrutin      TEXT NOT NULL,
    code_bloc         TEXT NOT NULL REFERENCES dim_bloc(code_bloc),
    part_predite      REAL NOT NULL,
    est_bloc_en_tete  INTEGER NOT NULL,
    modele            TEXT NOT NULL,
    PRIMARY KEY (code_commune, annee_cible, code_bloc)
);
CREATE INDEX ix_resultat_scrutin ON fait_resultat(id_scrutin, code_bloc);
CREATE INDEX ix_delinquance_annee ON fait_delinquance(annee);

-- Vue analytique : part de voix et bloc en tête par commune et par scrutin
CREATE VIEW v_resultats AS
SELECT r.code_commune, c.libelle, r.id_scrutin, r.code_bloc, r.voix,
       ROUND(100.0 * r.voix / p.exprimes, 2) AS part_pct,
       ROUND(100.0 * p.votants / p.inscrits, 2) AS participation_pct,
       RANK() OVER (PARTITION BY r.code_commune, r.id_scrutin ORDER BY r.voix DESC) AS rang
FROM fait_resultat r
JOIN fait_participation p USING (code_commune, id_scrutin)
JOIN dim_commune c USING (code_commune)
WHERE p.exprimes > 0;
