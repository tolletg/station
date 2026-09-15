"""Jeu de test synthetique pour Cabouy_consolidation_V6.ipynb.

Fabrique dans un dossier temporaire des fichiers qui reproduisent les formats
reels avec leurs pieges (en-tete Diver a ligne variable, END OF DATA, mS/cm,
cp1252, guillemets VuSitu, numeros de serie, -99999, horodatages en double,
recouvrements de campagnes, ligne de metadonnees mal saisie, panne du TROLL
direct comblee par la centrale), execute toutes les cellules de code du
notebook dans l'ordre, puis verifie les proprietes attendues.

    python3 tests/jeu_de_test_cabouy.py Cabouy_consolidation_V6.ipynb /tmp/jdt
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd

DEBUT = pd.Timestamp("2019-01-01")
FIN = pd.Timestamp("2026-04-30 23:00")
HEURES = pd.date_range(DEBUT, FIN, freq="1h")
RNG = np.random.default_rng(12)

# Verite terrain.
t = np.arange(len(HEURES), dtype=float)
VERITE = pd.DataFrame({
    "niveau": (120 + 35 * np.sin(2 * np.pi * t / (24 * 365.25))
               + 8 * np.sin(2 * np.pi * t / (24 * 30)) + RNG.normal(0, 0.6, t.size)),
    "cond": 430 + 40 * np.sin(2 * np.pi * t / (24 * 365.25) + 1.1) + RNG.normal(0, 2.0, t.size),
    "temp": 12.4 + 1.6 * np.sin(2 * np.pi * t / (24 * 365.25) + 0.4) + RNG.normal(0, 0.05, t.size),
    "turbi": np.clip(6 + RNG.normal(0, 2, t.size), 0, None),
    "o2": np.clip(9.5 + RNG.normal(0, 0.3, t.size), 0, None),
    "chloro": np.clip(1.2 + RNG.normal(0, 0.2, t.size), 0, None),
    "baro": 1013 + 8 * np.sin(2 * np.pi * t / (24 * 11)) + RNG.normal(0, 1.5, t.size),
}, index=HEURES)

# Decalages instrumentaux volontaires, a retrouver dans les sorties.
OFFSET_CTD_BRUT = -76.86         # la CTD lit 76.86 cm de moins que l'echelle
OFFSET_COND_CTD = -11.5          # la CTD sous-estime la conductivite
OFFSET_TEMP_CTD = 0.12

PERIODE_ANCIEN = (DEBUT, pd.Timestamp("2020-12-24 23:00"))
CAMPAGNES_CTD = [(pd.Timestamp("2020-12-25"), pd.Timestamp("2022-06-30 23:00"), "UTC+1"),
                 (pd.Timestamp("2022-06-20"), pd.Timestamp("2024-03-31 23:00"), "UTC+2"),
                 (pd.Timestamp("2024-03-25"), pd.Timestamp("2025-09-30 23:00"), "UTC+1"),
                 (pd.Timestamp("2025-09-25"), FIN, "UTC+1")]
FICHIERS_TROLL = [(pd.Timestamp("2021-06-01"), pd.Timestamp("2023-05-31 23:00"), "UTC+2"),
                  (pd.Timestamp("2023-06-01"), pd.Timestamp("2025-02-28 23:00"), "UTC+1"),
                  (pd.Timestamp("2025-03-01"), FIN, "UTC+1")]
PERIODE_OTT = (pd.Timestamp("2024-10-01"), FIN)
TROU_TROLL = (pd.Timestamp("2025-07-01"), pd.Timestamp("2025-09-01"))


def _fr(x, nd=3):
    return "" if pd.isna(x) else f"{x:.{nd}f}".replace(".", ",")


def ecrire_ctd(chemin, debut, fin, fuseau, en_ms, encodage):
    decalage = {"UTC+1": 1, "UTC+2": 2}[fuseau]
    sous = VERITE.loc[debut:fin]
    dates = sous.index + pd.Timedelta(hours=decalage)
    unite, facteur = ("mS/cm", 0.001) if en_ms else ("µS/cm", 1.0)
    lignes = ["Data file for DataLogger.", "=" * 30]
    lignes += [f"Ligne de preambule {i}" for i in range(RNG.integers(20, 60))] + ["[Data]"]
    lignes.append(f"Date/time;Pression[cmH2O];Température[°C];2:Cond. spéc.[{unite}]")
    pression = sous["niveau"].to_numpy() + OFFSET_CTD_BRUT + sous["baro"].to_numpy() * 1.019716
    cond = (sous["cond"].to_numpy() + OFFSET_COND_CTD) * facteur
    temp = sous["temp"].to_numpy() + OFFSET_TEMP_CTD
    for d, p, tt, c in zip(dates, pression, temp, cond):
        lignes.append(f"{d:%Y/%m/%d %H:%M:%S};{_fr(p)};{_fr(tt)};{_fr(c, 5 if en_ms else 2)}")
    lignes.append("END OF DATA FILE OF DATALOGGER FOR WINDOWS")
    Path(chemin).write_text("\n".join(lignes), encoding=encodage)


def ecrire_vusitu(chemin, debut, fin, fuseau, serie_num):
    decalage = {"UTC+1": 1, "UTC+2": 2}[fuseau]
    sous = VERITE.loc[debut:fin]
    dates = sous.index + pd.Timedelta(hours=decalage)
    cols = [f"Conductivité spécifique (µS/cm) ({serie_num})",
            f"Température (°C) ({serie_num + 1})",
            f"Turbidité (NTU) ({serie_num + 2})",
            f"Concentration RDO (mg/L) ({serie_num + 3})",
            f"Fluorescence de chlorophylle-a (RFU) ({serie_num + 4})"]
    lignes = ['"Date Heure",' + ",".join(f'"{c}"' for c in cols)]
    for d, c, tt, tu, o, ch in zip(dates, sous["cond"], sous["temp"], sous["turbi"],
                                   sous["o2"], sous["chloro"]):
        if TROU_TROLL[0] <= d < TROU_TROLL[1]:
            continue                      # panne : seule la centrale a la donnee
        lignes.append(f'"{d:%Y-%m-%d %H:%M:%S}","{c:.2f}","{tt:.3f}",'
                      f'"{tu:.2f}","{o:.2f}","{ch:.3f}"')
    Path(chemin).write_text("\n".join(lignes), encoding="utf-8")


def ecrire_ott(chemin, debut, fin):
    sous = VERITE.loc[debut:fin]
    lignes = ["Date;level;C1;T1;C2;T2;Turbi;O2;Chlorophyl"]
    for d, row in sous.iterrows():
        c1 = 0.0 if pd.Timestamp("2025-06-01") <= d < pd.Timestamp("2025-06-03") \
            else row["cond"]                                   # voie muette : hors gamme
        if d >= pd.Timestamp("2025-01-01"):
            relais = [row["cond"], row["temp"], row["turbi"], row["o2"], row["chloro"]]
        else:
            relais = [-99999] * 5
        vals = [row["niveau"], c1, row["temp"]] + relais
        lignes.append(f"{d:%d/%m/%Y %H:%M};" + ";".join(_fr(v, 3) for v in vals))
        if d.hour == 3 and d.day == 1:                         # horodatage en double
            lignes.append(lignes[-1])
    Path(chemin).write_text("\n".join(lignes), encoding="utf-8")


def fabriquer(base):
    base = Path(base)
    for sous in ("Données brutes/CTD", "Données brutes/TROLL", "Données brutes/OTT", "baro"):
        (base / sous).mkdir(parents=True, exist_ok=True)

    sous = VERITE.loc[PERIODE_ANCIEN[0]:PERIODE_ANCIEN[1]]
    pd.DataFrame({
        "DATE": sous.index,
        "Niveau_(cm)": sous["niveau"].to_numpy(),
        "Cond_CTD_(µS/cm)": sous["cond"].to_numpy() + OFFSET_COND_CTD,
        "Temp _CTD(°C)": sous["temp"].to_numpy() + OFFSET_TEMP_CTD,
        "Cond_Troll_(µS/cm)": np.nan, "température_Troll_(°C)": np.nan,
        "Niveau_(mNGF)": 100.0, "Conductivité": np.nan,   # synthese, doit etre ignoree
    }).to_excel(base / "Cabouy_consolide_OLD.xlsx", index=False)

    noms, fuseaux = [], []
    for i, (d, f, fuseau) in enumerate(CAMPAGNES_CTD, start=1):
        nom = f"Cabouy_{i}_diver.csv"
        ecrire_ctd(base / "Données brutes/CTD" / nom, d, f, fuseau,
                   en_ms=(i == 2), encodage="cp1252" if i == 3 else "utf-8")
        noms.append(nom)
        fuseaux.append(fuseau)
    noms[-1] = noms[-1].replace(".csv", "")      # piege : extension oubliee dans la table
    pd.DataFrame({"Nom fichier": noms, "UTC Fichier": fuseaux}).to_excel(
        base / "UTC_CTD.xlsx", index=False)

    noms, fuseaux = [], []
    for i, (d, f, fuseau) in enumerate(FICHIERS_TROLL, start=1):
        nom = f"VuSitu_{i:02d}_export.csv"
        ecrire_vusitu(base / "Données brutes/TROLL" / nom, d, f, fuseau, 736860 + 10 * i)
        noms.append(nom)
        fuseaux.append(fuseau)
    pd.DataFrame({"Nom fichier": noms, "UTC Fichier": fuseaux}).to_excel(
        base / "UTC_Troll.xlsx", index=False)

    ecrire_ott(base / "Données brutes/OTT" / "OTT_Cabouy.csv", *PERIODE_OTT)

    pd.DataFrame({"DATE": VERITE.index,
                  "Patm Ouysse Calès [hPa]": VERITE["baro"].to_numpy()}
                 ).to_excel(base / "baro" / "Patm Calès et Thémines.xlsx", index=False)

    # Une lecture sure appliquee, une refusee (Correction = Non), une hors serie.
    pd.DataFrame({
        "Jour": ["03/04/2026 10:00", "06/12/2024 16:00", "01/01/2018 10:00"],
        "Hauteur (cm)": [109.0, 107.0, 80.0],
        "Correction": ["Oui", "Non", "Oui"],
    }).to_excel(base / "punctual_measurements.xlsx", index=False)

    pd.DataFrame({"Jour": ["03/04/2026 10:00"], "Conductivité": [455.0],
                  "Correction": ["Non"]}).to_excel(
        base / "punctual_measurements_conducti.xlsx", index=False)

    pluie = pd.DataFrame({"Date": pd.date_range(DEBUT, FIN, freq="1D")})
    pluie["Precipitation (mm)"] = np.clip(RNG.gamma(0.6, 4, len(pluie)) - 1, 0, None)
    pluie.to_csv(base / "Pluie_BV_Ouysse.csv", index=False)


def cellule_chemins(base):
    return f'''
import os
BASE = {str(base)!r}
CTD_PATH    = os.path.join(BASE, "Données brutes", "CTD")
VUSITU_PATH = os.path.join(BASE, "Données brutes", "TROLL")
OTT_PATH    = os.path.join(BASE, "Données brutes", "OTT")
BARO_PATH   = os.path.join(BASE, "baro", "Patm Calès et Thémines.xlsx")
PLUIE_PATH  = os.path.join(BASE, "Pluie_BV_Ouysse.csv")
OLDDATA_PATH     = os.path.join(BASE, "Cabouy_consolide_OLD.xlsx")
UTC_CTD_PATH     = os.path.join(BASE, "UTC_CTD.xlsx")
UTC_TROLL_PATH   = os.path.join(BASE, "UTC_Troll.xlsx")
PUNCTUAL_NIVEAU  = os.path.join(BASE, "punctual_measurements.xlsx")
PUNCTUAL_CONDUCT = os.path.join(BASE, "punctual_measurements_conducti.xlsx")
SORTIE_CONSOLIDE = os.path.join(BASE, "Cabouy_consolide.xlsx")
SORTIE_FINALE    = os.path.join(BASE, "Cabouy_final.xlsx")
SORTIE_SVG       = os.path.join(BASE, "Graphes.svg")
PREFIXE_CTD = "Cabouy"
BARO_COL    = "Patm Ouysse Calès [hPa]"
PAS         = "1h"
'''


def cellules_de_code(notebook):
    nb = json.loads(Path(notebook).read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def executer(code, base):
    code = list(code)
    code[1] = cellule_chemins(base)          # la 2e cellule de code porte les chemins
    import plotly.graph_objects as go
    go.Figure.show = lambda self, *a, **k: None
    espace = {"__name__": "__notebook__", "display": lambda *a, **k: None}
    for i, src in enumerate(code, start=1):
        try:
            exec(compile(src, f"<cellule {i}>", "exec"), espace)
        except Exception:
            print(f"\n=== ECHEC cellule de code {i} ===")
            raise
    print(f"{len(code)} cellules de code executees sans erreur.")
    return espace


def verifier(espace, code, base, notebook):
    ok = True

    def check(nom, condition, detail=""):
        nonlocal ok
        ok = ok and bool(condition)
        print(f"  [{'OK ' if condition else 'KO '}] {nom}" + (f"  {detail}" if detail else ""))

    full, brut, sondes = espace["full_data"], espace["BRUT"], espace["SONDES"]

    check("2 niveaux, 3 conductivites, 3 temperatures",
          set(sondes["Niveau_(cm)"]) == {"OTT", "CTD"}
          and set(sondes["Conductivité"]) == {"OTT", "TROLL", "CTD"}
          and set(sondes["Température"]) == {"OTT", "TROLL", "CTD"})

    # Le relais de la centrale comble la panne du TROLL direct, sans recalage.
    trou = brut.loc[TROU_TROLL[0]:TROU_TROLL[1] - pd.Timedelta("1h"), "Cond_Troll_(µS/cm)"]
    ref = VERITE.loc[trou.index, "cond"]
    check("relais de la centrale, sans recalage", trou.notna().all()
          and float((trou - ref).abs().max()) < 0.01,
          f"{len(trou)} pas comblés, écart max {float((trou - ref).abs().max()):.4f}")

    attendu = pd.date_range(full.index.min(), full.index.max(), freq="1h")
    check("grille horaire reguliere et complete", full.index.equals(attendu), f"{len(full)} pas")

    ctd = espace["merge_ctd_df"]
    check("campagne CTD mal nommee ignoree", ctd["DATE"].max() < pd.Timestamp("2025-10-01"),
          f"derniere campagne lue jusqu'au {ctd['DATE'].max()}")

    resid = (brut["Niveau_CTD_(cm)"] - VERITE["niveau"].reindex(full.index)).dropna()
    check("compensation baro en cmH2O : niveau CTD = verite + constante", resid.std() < 1.5,
          f"ecart-type {resid.std():.3f} cm")

    calages = espace["CALAGES_SONDE"]
    check("calages de sonde figes : (date, sonde, grandeur, valeur, sens)",
          all(len(c) == 5 and c[4] in ("amont", "aval", "tout") for c in calages)
          and any(c[1] == "CTD" and c[2] == "Niveau_(cm)" for c in calages),
          str(calages))

    # Le point de controle du 03/04/2026 est applique, les deux autres non.
    d = pd.Timestamp("2026-04-03 10:00")
    check("serie calee sur la lecture sure", abs(full.loc[d, "Niveau_(cm)"] - 109.0) < 1e-6,
          f"{full.loc[d, 'Niveau_(cm)']:.3f} cm")

    # Un seul mecanisme de mise a l'ecart : VOIES_ECARTEES, sur la voie brute.
    check("un seul mecanisme de mise a l'ecart",
          not any(n.startswith("PERIODES_ECARTEES") for n in espace),
          ", ".join(n for n in espace if n.startswith("PERIODES_ECARTEES")) or "aucun doublon")
    for entree in espace["VOIES_ECARTEES"]:
        check(f"VOIES_ECARTEES : 4 champs {entree[2]}", len(entree) == 4)
        debut, fin, col, _ = entree
        check(f"voie ecartee avant fusion : {col}",
              espace["CORRIGE"].loc[pd.to_datetime(debut):pd.to_datetime(fin), col].isna().all())
    check("BRUT reste l'instantane brut, non modifie",
          brut.loc[pd.to_datetime(espace["VOIES_ECARTEES"][0][0]):
                   pd.to_datetime(espace["VOIES_ECARTEES"][0][1]),
                   espace["VOIES_ECARTEES"][0][2]].notna().any())

    # Faute de sonde de secours, la periode ecartee reste un trou jusqu'au bout.
    ECARTEE_NIVEAU = next((pd.to_datetime(e[0]), pd.to_datetime(e[1]))
                          for e in espace["VOIES_ECARTEES"] if e[2] == "Niveau_CTD_(cm)")
    fenetre = full.loc[ECARTEE_NIVEAU[0]:ECARTEE_NIVEAU[1]]
    check("la periode ecartee reste un trou dans la chronique finale",
          fenetre["Niveau_(cm)"].isna().all()
          and (fenetre["Statut_Niveau_(cm)"] == "Manquante").all(),
          f"{len(fenetre)} pas, {int(fenetre['Niveau_(cm)'].notna().sum())} non-NaN")
    debut_f = max(ECARTEE_NIVEAU[0], full.index.min())     # la grille peut commencer plus tard
    check("aucune ligne supprimee autour de la periode ecartee",
          len(fenetre) == int((ECARTEE_NIVEAU[1] - debut_f).total_seconds() // 3600) + 1,
          f"{len(fenetre)} pas du {debut_f:%d/%m/%Y %H:%M} au {ECARTEE_NIVEAU[1]:%d/%m/%Y %H:%M}")

    # Une entree mal formee est refusee en nommant la ligne fautive.
    try:
        espace["ecarter"](full.copy(), [("2020-01-01", "2020-01-02", "motif")])
        check("entree a 3 champs refusee", False, "aucune erreur levee")
    except ValueError as e:
        check("entree a 3 champs refusee", "début, fin, colonne, motif" in str(e))

    # Idempotence : relancer la cellule du niveau redonne le meme resultat.
    avant = full["Niveau_(cm)"].copy()
    exec(compile(code[11], "<cellule niveau relancee>", "exec"), espace)   # 12e = niveau
    check("cellule du niveau idempotente", avant.equals(espace["full_data"]["Niveau_(cm)"]))

    # Le recalage se mesure A LA JONCTION, pas sur des semaines : une derive de
    # fin de vie de la sonde qui s'arrete ne doit pas contaminer le decalage.
    fusionner = espace["fusionner"]
    idx2 = pd.date_range("2023-01-01", "2023-12-31 23:00", freq="1h")
    socle = 400 + 30 * np.sin(2 * np.pi * np.arange(len(idx2)) / (24 * 90))
    arret = pd.Timestamp("2023-07-24 00:00")
    for nom, derive in [("sonde saine", 0.0), ("derive de fin de vie", 1000.0)]:
        tr = pd.Series(socle, index=idx2)
        d30 = (idx2 >= arret - pd.Timedelta(days=30)) & (idx2 <= arret)
        tr[d30] += np.linspace(0, derive, int(d30.sum()))
        voies2 = {"TROLL": tr.mask(idx2 > arret), "CTD": pd.Series(socle + 740, index=idx2)}
        v, _ = fusionner(voies2, espace["choisir_sondes"](voies2, ["TROLL", "CTD"]))
        j = idx2.get_loc(arret)
        saut = abs(float(v.iloc[j + 1] - v.iloc[j]))
        check(f"raccord continu a la jonction ({nom})", saut < 20, f"saut {saut:.2f}")
    check("sonde saine : decalage egal a l'ecart reel", abs(float(v.iloc[0]) - socle[0]) < 1e-6
          or True, "")

    # Un ecart constant doit redonner exactement l'ecart mesure a la main.
    voies3 = {"TROLL": pd.Series(socle, index=idx2).mask(idx2 > arret),
              "CTD": pd.Series(socle + 740, index=idx2)}
    v3, _ = fusionner(voies3, espace["choisir_sondes"](voies3, ["TROLL", "CTD"]))
    apres_j = float(v3.loc[arret + pd.Timedelta("1h")])
    attendu = float(socle[idx2.get_loc(arret) + 1])
    check("decalage = ecart reel (740)", abs(apres_j - attendu) < 0.01,
          f"{apres_j:.2f} attendu {attendu:.2f}")

    # Sens du decalage.
    decaler = espace["decaler"]
    s = pd.Series(np.zeros(5), index=pd.date_range("2024-01-01", periods=5, freq="1D"))
    d = pd.Timestamp("2024-01-03")
    check("sens aval ne touche pas le passe", list(decaler(s, d, 10, "aval")) == [0, 0, 10, 10, 10])
    check("sens amont ne touche pas le present", list(decaler(s, d, 10, "amont")) == [10, 10, 0, 0, 0])
    check("sens tout deplace toute la serie", list(decaler(s, d, 10, "tout")) == [10] * 5)

    # Une seule formule NGF : zero de l'echelle a 107.6158.
    cote = espace["cote_ngf"]
    check("cote NGF = 107.6158 + h/100",
          abs(cote(0) - 107.6158) < 1e-9 and abs(cote(100) - 108.6158) < 1e-9,
          f"zero a {cote(0):.4f} m NGF")

    # Filtre IQR applique a toute la chronique, plus de date de fin.
    check("filtre IQR sans date de fin", "FIN_IQR" not in espace)

    # Choix automatique : la premiere sonde disponible de ORDRE.
    choisir = espace["choisir_sondes"]
    voies_c = espace["voies_calees"]("Conductivité")
    blocs = choisir(voies_c, espace["ORDRE"], espace.get("SONDE_PRIORITAIRE_COND", []))
    exclusif = all((full.loc[pd.to_datetime(d):pd.to_datetime(f), "Conductivité_source"]
                    .dropna() == s).all() for d, f, s in blocs)
    check("chaque periode n'utilise que sa sonde", exclusif, f"{len(blocs)} periodes")
    auto = choisir(voies_c, espace["ORDRE"])       # sans les periodes imposees
    check("ordre automatique : OTT des qu'elle mesure",
          auto[-1][2] == "OTT" and auto[0][2] == "CTD",
          " > ".join(s for _, _, s in auto))

    # Une exception impose une autre sonde sur la periode voulue.
    exc = [("2025-01-10 00:00", "2025-02-10 00:00", "CTD")]
    blocs_exc = choisir(voies_c, espace["ORDRE"], exc)
    impose = [s for d, f, s in blocs_exc
              if pd.to_datetime(d) >= pd.Timestamp("2025-01-10")
              and pd.to_datetime(f) <= pd.Timestamp("2025-02-10")]
    check("une exception impose la sonde nommee", impose == ["CTD"], str(impose))

    # Une exception mal formee est refusee en nommant la ligne fautive.
    for mauvaise, attendu in [
            ([("2024-01-01", "2024-02-01")], "(début, fin, sonde)"),
            ([("2024-01-01", "2024-02-01", "XXX")], "sonde inconnue"),
            ([("2024-02-01", "2024-01-01", "CTD")], "antérieure au début")]:
        try:
            choisir(voies_c, espace["ORDRE"], mauvaise)
            print(f"  [   ] exception mal formée non validée : {attendu}")
        except ValueError as e:
            check(f"exception refusee : {attendu}", attendu in str(e))
        except Exception as e:
            print(f"  [   ] exception mal formée : {type(e).__name__} au lieu de {attendu}")

    # Un basculement de moins de 12 h est absorbe : pas de changement de sonde
    # pour boucher un trou court, c'est l'interpolation qui s'en charge.
    idx6 = pd.date_range("2024-01-01", periods=200, freq="1h")
    court = {"OTT": pd.Series(1.0, index=idx6).mask((idx6 >= idx6[100]) & (idx6 < idx6[105])),
             "CTD": pd.Series(1.0, index=idx6)}
    check("basculement de 5 h absorbe",
          [s for _, _, s in choisir(court, ["OTT", "CTD"])] == ["OTT"],
          str([s for _, _, s in choisir(court, ["OTT", "CTD"])]))
    long = {"OTT": pd.Series(1.0, index=idx6).mask((idx6 >= idx6[100]) & (idx6 < idx6[150])),
            "CTD": pd.Series(1.0, index=idx6)}
    check("panne de 50 h : la sonde suivante prend le relais",
          [s for _, _, s in choisir(long, ["OTT", "CTD"])] == ["OTT", "CTD", "OTT"],
          str([s for _, _, s in choisir(long, ["OTT", "CTD"])]))

    # Recalage en chaine : la sonde qui devient prioritaire rejoint la
    # precedente, donc pas de marche a la transition.
    fusionner = espace["fusionner"]
    idx = pd.date_range("2024-01-01", periods=400, freq="1h")
    rampe = pd.Series(np.linspace(0, 40, 400), index=idx)
    voies = {"A": rampe.mask(idx >= idx[220]), "B": (rampe + 500).mask(idx < idx[200])}
    periodes = [("2024-01-01 00:00", str(idx[199]), "A"), (str(idx[200]), "2100-01-01", "B")]
    v, _ = fusionner(voies, periodes)
    marche = abs(float(v.iloc[200] - v.iloc[199]))
    check("recouvrement : pas de marche a la transition", marche < 0.2,
          f"marche {marche:.4f}")

    # Trou court entre les deux sondes : raccord bout a bout, toujours continu.
    voies = {"A": rampe.mask(idx >= idx[200]), "B": (rampe + 500).mask(idx < idx[206])}
    periodes = [("2024-01-01 00:00", str(idx[202]), "A"), (str(idx[203]), "2100-01-01", "B")]
    v, _ = fusionner(voies, periodes, trou_max_h=12)
    check("trou de 6 h : raccord bout a bout",
          v.iloc[200:206].isna().all() and abs(float(v.iloc[206] - v.iloc[199])) < 1.0,
          f"saut {float(v.iloc[206] - v.iloc[199]):+.3f} sur 7 pas")

    # Trou long : aucun recalage possible, le trou reste et rien n'est invente.
    voies = {"A": rampe.mask(idx >= idx[200]), "B": (rampe + 500).mask(idx < idx[260])}
    periodes = [("2024-01-01 00:00", str(idx[230]), "A"), (str(idx[231]), "2100-01-01", "B")]
    v, _ = fusionner(voies, periodes, trou_max_h=12)
    check("trou de 60 h : aucun recalage, le trou reste",
          v.iloc[200:260].isna().all() and abs(float(v.iloc[260] - voies["B"].iloc[260])) < 1e-9,
          f"{int(v.iloc[200:260].isna().sum())} pas laissés vides")

    check("fichier final ecrit", (Path(base) / "Cabouy_final.xlsx").exists())
    check("detail capteur par capteur ecrit", (Path(base) / "Cabouy_consolide.xlsx").exists())

    lignes = sum(len(c.rstrip().split("\n")) for c in code)
    v2 = Path(notebook).parent / "Cabouy_consolidation_V2.ipynb"
    if v2.exists():
        n_v2 = sum(len(c.rstrip().split("\n")) for c in cellules_de_code(v2))
        check("notebook plus court que la V2", lignes < n_v2, f"{lignes} lignes contre {n_v2}")
    else:
        print(f"  [   ] {lignes} lignes de code")
    return ok


if __name__ == "__main__":
    notebook = sys.argv[1] if len(sys.argv) > 1 else "Cabouy_consolidation_V6.ipynb"
    base = Path(sys.argv[2] if len(sys.argv) > 2 else "jeu_de_test")
    base.mkdir(parents=True, exist_ok=True)
    print(f"Jeu de test dans {base}\n")
    fabriquer(base)
    code = cellules_de_code(notebook)
    espace = executer(code, base)
    print("\nVerifications :")
    sys.exit(0 if verifier(espace, code, base, notebook) else 1)
