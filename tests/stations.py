# -*- coding: utf-8 -*-
"""Configuration par station pour la generation des notebooks."""

RACINE = r"Y:\MISSIONS\Eau\1 - Projet Hydrogéologique Ouysse\3 - Hydrodynamique\0 - Stations en continu"
BARO = RACINE + r"\1 - Données BARO\Gourdon baro\Patm Calès et Thémines.xlsx"
PLUIE = RACINE + r"\Saint Sauveur\Gaetan\Données brutes\Pluie_BV_Ouysse.csv"

STANDARD = {"Niveau_(cm)": "Niveau_CTD_(cm)"}

STATIONS = {}

STATIONS["Fontbelle"] = dict(
    fichier="Code pour consolider les données-Fontbelle_V4.ipynb",
    titre="Fontbelle",
    base=RACINE + r"\Fontbelle\Gaetan",
    prefixe="Fontbelle",
    troll=True, ott=True,
    olddata="Fontbelle__consolide_OLD.xlsx", old_csv=False,
    renommage_old=dict(STANDARD),
    punctual_niveau="punctual_measurements_Niveau.xlsx",
    punctual_cond="punctual_measurements_Conducti.xlsx",
    sortie_consolide="Fontbelle_consolide.xlsx",
    sortie_finale="Fontbelle_final.xlsx",
    ordre=["TROLL", "OTT", "CTD"],
    ngf=None,
    iqr=("48h", 0.8), lissage=0,
    tarage=dict(
        unite="L/s", seuil=26.1,
        corps=('    Q = np.where(h > SEUIL_H, 0.0008 * h**2 - 0.0528 * h + 0.9079,\n'
               '                 0.0027 * h + 0.0032) * 1000'),
        note="Deux branches raccordees a H = 26.1 cm (0.0737 contre 0.0748 m3/s au seuil)."),
    voies_ecartees=[
        ("2019-04-18 12:00", "2019-04-18 12:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2020-07-29 14:00", "2020-07-29 15:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2020-09-23 13:00", "2020-09-23 13:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2019-02-27 15:00", "2019-04-05 12:00", "Cond_CTD_(µS/cm)", "CTD hors d'eau"),
        ("2019-06-27 10:00", "2019-10-23 18:00", "Cond_CTD_(µS/cm)", "dérive CTD après nettoyage"),
        ("2023-06-20 13:00", "2023-09-05 12:00", "Cond_Troll_(µS/cm)", "TROLL encrassée"),
        ("2024-12-05 02:00", "2024-12-05 18:00", "Cond_Troll_(µS/cm)", "pic anormal"),
        ("2024-12-05 02:00", "2024-12-05 18:00", "Cond_CTD_(µS/cm)", "pic anormal"),
    ],
    calages=[],
)

STATIONS["Saint-Sauveur"] = dict(
    fichier="Code pour consolider les données-Saint_Sauveur_V3.ipynb",
    titre="Saint-Sauveur",
    base=RACINE + r"\Saint Sauveur\Gaetan",
    prefixe="Saint Sauveur",
    troll=True, ott=False,
    olddata="Saint Sauveur_consolide_OLD.xlsx", old_csv=False,
    renommage_old=dict(STANDARD),
    punctual_niveau="punctual_measurements _Mod.xlsx",
    punctual_cond="punctual_measurements_original.xlsx",
    sortie_consolide="Saint_Sauveur_consolide.xlsx",
    sortie_finale="Saint_Sauveur_final.xlsx",
    ordre=["TROLL", "CTD"],
    ngf=107.611,
    iqr=("48h", 0.8), lissage=0,
    tarage=None,
    voies_ecartees=[
        ("2020-06-07 14:00", "2020-06-07 14:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2021-09-09 12:00", "2021-09-09 13:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2019-03-19 21:00", "2019-03-31 14:00", "Cond_Troll_(µS/cm)", "valeurs aberrantes"),
        ("2019-03-19 21:00", "2019-03-31 14:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
    ],
    calages=[],
)

STATIONS["Thémines"] = dict(
    fichier="Code pour consolider les données-Thémines_V2.ipynb",
    titre="Thémines",
    base=RACINE + r"\Thémines\Gaetan",
    prefixe="Thémines",
    troll=True, ott=False,
    olddata="Themine_consolide_OLD.csv", old_csv=True,
    renommage_old={"Niveau": "Niveau_CTD_(cm)", "Conducti": "Cond_CTD_(µS/cm)",
                   "Temp": "Temp _CTD(°C)", "Xtroll": "Cond_Troll_(µS/cm)",
                   "TempTroll": "température_Troll_(°C)", "Turbidity": "Turbidity_Troll_(NTU)",
                   "O2": "O2_Troll_(mg/l)",
                   "FluoChloro_a": "FluorescenceChloro_a_Troll_(RFU)"},
    punctual_niveau="punctual_measurements_Niveau.xlsx",
    punctual_cond="punctual_measurements_Brute.xlsx",
    sortie_consolide="Themines_consolide.xlsx",
    sortie_finale="Themines_final.xlsx",
    ordre=["CTD", "TROLL"],
    ngf=311.261,
    iqr=("48h", 0.0), lissage=0,
    tarage=dict(
        unite="L/s", seuil=21.4,
        corps=('    Q = np.where(h >= SEUIL_H, 8325.3 * (h / 100)**2 - 2266.1 * (h / 100) + 116.21,\n'
               '                 50.485 * (h / 100) + 1)'),
        note="Deux branches raccordees a H = 21.4 cm, hauteur en metres dans les deux formules."),
    voies_ecartees=[
        ("2024-03-07 11:00", "2024-03-07 11:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2020-01-21 12:00", "2020-01-21 12:00", "Niveau_CTD_(cm)", "pic isolé"),
        ("2019-02-27 17:00", "2019-03-30 11:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2024-07-31 11:00", "2024-09-18 16:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
    ],
    calages=[],
)

STATIONS["Ouysse"] = dict(
    fichier="Code pour consolider les données-Ouysse_V3.ipynb",
    titre="Ouysse - Calès",
    base=RACINE + r"\Ouysse - Calès\Gaetan",
    prefixe="Ouysse",
    troll=False, ott=False,
    olddata="OuysseCales_consolide_old.xlsx", old_csv=False,
    utc_ctd=r"Données brutes\UTC_CTD.xlsx",
    renommage_old={"Niveau": "Niveau_CTD_(cm)", "Conducti": "Cond_CTD_(µS/cm)",
                   "Temp": "Temp _CTD(°C)"},
    punctual_niveau="punctual_measurements.xlsx",
    punctual_cond="punctual_measurements.xlsx",
    sortie_consolide="OuysseCales_consolide.xlsx",
    sortie_finale="OuysseCales_final.xlsx",
    ordre=["CTD"],
    ngf=None,
    iqr=("500h", 0.8), lissage=0,
    tarage=dict(
        unite="m3/s", seuil=100.0,
        corps=('    Q = np.where(h >= SEUIL_H, 10.227 * (h / 100)**2 + 7.3348 * (h / 100) - 10,\n'
               '                 7.7563 * (h / 100)**7.6404)'),
        note="Deux branches raccordees a H = 1 m, hauteur en metres dans les deux formules."),
    voies_ecartees=[
        ("2021-01-23 12:00", "2021-01-26 15:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2021-01-29 08:00", "2021-02-04 16:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2021-02-10 03:00", "2021-02-14 14:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2023-11-03 00:00", "2023-11-07 07:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2023-11-09 21:00", "2023-11-14 02:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2023-12-11 09:00", "2023-12-15 08:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
        ("2024-05-01 13:00", "2024-05-09 19:00", "Cond_CTD_(µS/cm)", "valeurs aberrantes"),
    ],
    calages=[],
)
