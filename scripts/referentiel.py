"""Données de référence du projet (référentiel) : passage COG et rattachement des nuances aux blocs politiques.
Utilisé par les scripts 02 (transformation), 06 (cartes) et 07 (base SQL)."""

# --- Table de passage COG : communes fusionnées depuis 2017 -> commune nouvelle (COG 2025)
PASSAGE_COG = {
    "38016": "38479", "38121": "38479", "38274": "38479",  # Arzay, Commelle, Nantoin -> Porte-des-Bonnevaux
    "38025": "38284",                                        # Balbins -> Ornacieux-Balbins
    "38293": "38560",                                        # Panissage -> Val-de-Virieu
    "38302": "38073",                                        # Le Périer -> Chantepérier
    "38306": "38163",                                        # Pinsot -> Le Haut-Bréda
    "38367": "38395", "38435": "38395",                      # Saint-Bernard, Saint-Pancrasse -> Plateau-des-Petites-Roches
}

# --- Référentiel des blocs politiques (données de référence)
BLOC_NUANCE = {
    # Gauche
    **{n: "GAUCHE" for n in ["EXG", "DXG", "COM", "FI", "SOC", "RDG", "VEC", "DVG", "UG", "ECO", "NUP"]},
    # Centre (majorité présidentielle)
    **{n: "CENTRE" for n in ["REM", "MDM", "REN", "HOR", "ENS", "DVC"]},
    # Droite
    **{n: "DROITE" for n in ["LR", "UDI", "DVD", "DSV", "DLF"]},
    # Extrême droite
    **{n: "EXTREME_DROITE" for n in ["FN", "RN", "REC", "UXD", "EXD", "DXD"]},
    # Autres
    **{n: "AUTRES" for n in ["DIV", "REG"]},
}
BLOC_PRES = {
    "ARTHAUD": "GAUCHE", "POUTOU": "GAUCHE", "ROUSSEL": "GAUCHE", "MÉLENCHON": "GAUCHE", "HAMON": "GAUCHE",
    "HIDALGO": "GAUCHE", "JADOT": "GAUCHE", "MACRON": "CENTRE", "FILLON": "DROITE", "PÉCRESSE": "DROITE",
    "DUPONT-AIGNAN": "DROITE", "LE PEN": "EXTREME_DROITE", "ZEMMOUR": "EXTREME_DROITE",
    "LASSALLE": "AUTRES", "ASSELINEAU": "AUTRES", "CHEMINADE": "AUTRES",
}
BLOC_EURO2019 = {
    "RENAISSANCE": "CENTRE", "LES EUROPÉENS": "CENTRE",
    "PRENEZ LE POUVOIR": "EXTREME_DROITE", "ENSEMBLE PATRIOTES": "EXTREME_DROITE", "LISTE DE LA RECONQUÊTE": "EXTREME_DROITE",
    "UNION DROITE-CENTRE": "DROITE", "DEBOUT LA FRANCE": "DROITE",
    "EUROPE ÉCOLOGIE": "GAUCHE", "ENVIE D'EUROPE": "GAUCHE", "LA FRANCE INSOUMISE": "GAUCHE", "LISTE CITOYENNE": "GAUCHE",
    "POUR L'EUROPE DES GENS": "GAUCHE", "URGENCE ÉCOLOGIE": "GAUCHE", "LUTTE OUVRIÈRE": "GAUCHE", "RÉVOLUTIONNAIRE": "GAUCHE",
}  # toute autre liste -> AUTRES

