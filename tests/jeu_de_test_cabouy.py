"""Jeu de test synthetique pour Cabouy_consolidation_V5.ipynb.

Fabrique, dans un dossier temporaire, des fichiers qui reproduisent les formats
reels (Diver, VuSitu, centrale OTT, baro, tables UTC, mesures ponctuelles) avec
leurs pieges : en-tete a ligne variable, END OF DATA, virgules decimales, mS/cm,
encodage cp1252, guillemets, numeros de serie, -99999, horodatages en double,
recouvrements de campagnes, ligne de metadonnees manquante.

Puis execute toutes les cellules de code du notebook dans l'ordre et verifie
quelques proprietes attendues.
"""
import json
import os
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

# Verite terrain : un niveau (cm au-dessus du zero du capteur), une conductivite,
# une temperature, plus les voies TROLL.
t = np.arange(len(HEURES), dtype=float)
NIVEAU = (120 + 35 * np.sin(2 * np.pi * t / (24 * 365.25))
          + 8 * np.sin(2 * np.pi * t / (24 * 30)) + RNG.normal(0, 0.6, t.size))
COND = (430 + 40 * np.sin(2 * np.pi * t / (24 * 365.25) + 1.1) + RNG.normal(0, 2.0, t.size))
TEMP = 12.4 + 1.6 * np.sin(2 * np.pi * t / (24 * 365.25) + 0.4) + RNG.normal(0, 0.05, t.size)
TURBI = np.clip(6 + RNG.normal(0, 2, t.size), 0, None)
O2 = np.clip(9.5 + RNG.normal(0, 0.3, t.size), 0, None)
CHLORO = np.clip(1.2 + RNG.normal(0, 0.2, t.size), 0, None)
BARO = 1013 + 8 * np.sin(2 * np.pi * t / (24 * 11)) + RNG.normal(0, 1.5, t.size)

VERITE = pd.DataFrame({"niveau": NIVEAU, "cond": COND, "temp": TEMP, "turbi": TURBI,
                       "o2": O2, "chloro": CHLORO, "baro": BARO}, index=HEURES)

# Decalages instrumentaux volontaires, a retrouver dans les journaux.
OFFSET_ANCIEN_FICHIER = 0.0      # l'ancien fichier est la reference historique
OFFSET_CTD_BRUT = -76.86         # la CTD lit 76.86 cm de moins que l'echelle
OFFSET_COND_TROLL = 0.0
OFFSET_COND_CTD = -11.5          # la CTD sous-estime la conductivite
OFFSET_COND_OTT = 0.0
OFFSET_TEMP_CTD = 0.12

# Periodes couvertes par chaque source.
PERIODE_ANCIEN = (DEBUT, pd.Timestamp("2020-12-24 23:00"))
CAMPAGNES_CTD = [(pd.Timestamp("2020-12-25"), pd.Timestamp("2022-06-30 23:00"), "UTC+1"),
                 (pd.Timestamp("2022-06-20"), pd.Timestamp("2024-03-31 23:00"), "UTC+2"),
                 (pd.Timestamp("2024-03-25"), pd.Timestamp("2025-09-30 23:00"), "UTC+1"),
                 (pd.Timestamp("2025-09-25"), FIN, "UTC+1")]
FICHIERS_TROLL = [(pd.Timestamp("2021-06-01"), pd.Timestamp("2023-05-31 23:00"), "UTC+2"),
                  (pd.Timestamp("2023-06-01"), pd.Timestamp("2025-02-28 23:00"), "UTC+1"),
                  (pd.Timestamp("2025-03-01"), FIN, "UTC+1")]
PERIODE_OTT = (pd.Timestamp("2024-10-01"), FIN)
# Panne des exports directs : seule la voie rapatriee par la centrale couvre.
TROU_TROLL = (pd.Timestamp("2025-07-01"), pd.Timestamp("2025-09-01"))


def _fr(x, nd=3):
    return "" if pd.isna(x) else f"{x:.{nd}f}".replace(".", ",")


def ecrire_ctd(chemin, debut, fin, fuseau, en_ms, encodage):
    """Export Diver : en-tete a longueur variable, virgules, END OF DATA."""
    decalage = {"UTC+1": 1, "UTC+2": 2}[fuseau]
    sous = VERITE.loc[debut:fin]
    dates = sous.index + pd.Timedelta(hours=decalage)     # horodatage local
    unite = "mS/cm" if en_ms else "µS/cm"
    facteur = 0.001 if en_ms else 1.0
    entete = ["Data file for DataLogger.", "=" * 30]
    entete += [f"Ligne de preambule {i}" for i in range(RNG.integers(20, 60))]
    entete += ["[Data]"]
    lignes = list(entete)
    lignes.append(f"Date/time;Pression[cmH2O];Température[°C];2:Cond. spéc.[{unite}]")
    pression = sous["niveau"].to_numpy() + OFFSET_CTD_BRUT + sous["baro"].to_numpy() * 1.019716
    cond = (sous["cond"].to_numpy() + OFFSET_COND_CTD) * facteur
    temp = sous["temp"].to_numpy() + OFFSET_TEMP_CTD
    for d, p, tt, c in zip(dates, pression, temp, cond):
        lignes.append(f"{d:%Y/%m/%d %H:%M:%S};{_fr(p)};{_fr(tt)};{_fr(c, 5 if en_ms else 2)}")
    lignes.append("END OF DATA FILE OF DATALOGGER FOR WINDOWS")
    Path(chemin).write_text("\n".join(lignes), encoding=encodage)


def ecrire_vusitu(chemin, debut, fin, fuseau, serie_num):
    """Export VuSitu : guillemets partout, numero de serie dans les libelles."""
    decalage = {"UTC+1": 1, "UTC+2": 2}[fuseau]
    sous = VERITE.loc[debut:fin]
    dates = sous.index + pd.Timedelta(hours=decalage)
    cols = [f"Conductivité spécifique (µS/cm) ({serie_num})",
            f"Température (°C) ({serie_num + 1})",
            f"Turbidité (NTU) ({serie_num + 2})",
            f"Concentration RDO (mg/L) ({serie_num + 3})",
            f"Fluorescence de chlorophylle-a (RFU) ({serie_num + 4})"]
    lignes = ['"Date Heure",' + ",".join(f'"{c}"' for c in cols)]
    for d, c, tt, tu, o, ch in zip(dates, sous["cond"] + OFFSET_COND_TROLL, sous["temp"],
                                   sous["turbi"], sous["o2"], sous["chloro"]):
        if TROU_TROLL[0] <= d < TROU_TROLL[1]:
            continue                    # panne du TROLL : seule la centrale a la donnee
        lignes.append(f'"{d:%Y-%m-%d %H:%M:%S}","{c:.2f}","{tt:.3f}",'
                      f'"{tu:.2f}","{o:.2f}","{ch:.3f}"')
    Path(chemin).write_text("\n".join(lignes), encoding="utf-8")


def ecrire_ott(chemin, debut, fin):
    """Centrale : -99999, horodatages en double, voies qui demarrent plus tard."""
    sous = VERITE.loc[debut:fin]
    lignes = ["Date;level;C1;T1;C2;T2;Turbi;O2;Chlorophyl"]
    debut_troll_relais = pd.Timestamp("2025-01-01")
    for d, row in sous.iterrows():
        level = row["niveau"]
        c1, t1 = row["cond"] + OFFSET_COND_OTT, row["temp"]
        if d >= debut_troll_relais:
            c2, t2 = row["cond"] + OFFSET_COND_TROLL, row["temp"]
            tu, o2, ch = row["turbi"], row["o2"], row["chloro"]
        else:
            c2 = t2 = tu = o2 = ch = -99999
        if pd.Timestamp("2025-06-01") <= d < pd.Timestamp("2025-06-03"):
            c1 = 0.0                                   # voie muette : hors gamme
        vals = [level, c1, t1, c2, t2, tu, o2, ch]
        lignes.append(f"{d:%d/%m/%Y %H:%M};" + ";".join(_fr(v, 3) for v in vals))
        if d.hour == 3 and d.day == 1:                 # horodatage en double
            lignes.append(lignes[-1])
    Path(chemin).write_text("\n".join(lignes), encoding="utf-8")


def fabriquer(base):
    base = Path(base)
    for sous in ("Données brutes/CTD", "Données brutes/TROLL", "Données brutes/OTT"):
        (base / sous).mkdir(parents=True, exist_ok=True)

    # Ancien fichier consolide : CTD + TROLL, deja fusionnes par la V2.
    sous = VERITE.loc[PERIODE_ANCIEN[0]:PERIODE_ANCIEN[1]]
    ancien = pd.DataFrame({
        "DATE": sous.index,
        "Niveau_(cm)": sous["niveau"].to_numpy() + OFFSET_ANCIEN_FICHIER,
        "Cond_CTD_(µS/cm)": sous["cond"].to_numpy() + OFFSET_COND_CTD,
        "Temp _CTD(°C)": sous["temp"].to_numpy() + OFFSET_TEMP_CTD,
        "Cond_Troll_(µS/cm)": np.nan, "température_Troll_(°C)": np.nan,
        "Niveau_(mNGF)": 100.0, "Conductivité": np.nan,     # synthese, doit etre ignoree
    })
    ancien.to_excel(base / "Cabouy_consolide_OLD.xlsx", index=False)

    noms_ctd, utc_ctd = [], []
    for i, (d, f, fuseau) in enumerate(CAMPAGNES_CTD, start=1):
        nom = f"Cabouy_{i}_diver.csv"
        ecrire_ctd(base / "Données brutes/CTD" / nom, d, f, fuseau,
                   en_ms=(i == 2), encodage="cp1252" if i == 3 else "utf-8")
        noms_ctd.append(nom)
        utc_ctd.append(fuseau)
    # Piege volontaire : la campagne 4 est saisie sans son extension.
    lignes_utc = list(zip(noms_ctd, utc_ctd))
    lignes_utc[-1] = (lignes_utc[-1][0].replace(".csv", ""), lignes_utc[-1][1])
    pd.DataFrame(lignes_utc, columns=["Nom fichier", "UTC Fichier"]).to_excel(
        base / "UTC_CTD.xlsx", index=False)

    noms_troll, utc_troll = [], []
    for i, (d, f, fuseau) in enumerate(FICHIERS_TROLL, start=1):
        nom = f"VuSitu_{i:02d}_export.csv"
        ecrire_vusitu(base / "Données brutes/TROLL" / nom, d, f, fuseau, 736860 + 10 * i)
        noms_troll.append(nom)
        utc_troll.append(fuseau)
    pd.DataFrame({"Nom fichier": noms_troll, "UTC Fichier": utc_troll}).to_excel(
        base / "UTC_Troll.xlsx", index=False)

    ecrire_ott(base / "Données brutes/OTT" / "OTT_Cabouy_2024_2026.csv", *PERIODE_OTT)

    baro_dir = base / "baro"
    baro_dir.mkdir(exist_ok=True)
    pd.DataFrame({"DATE": VERITE.index,
                  "Patm Ouysse Calès [hPa]": VERITE["baro"].to_numpy(),
                  "Patm Thémines [hPa]": VERITE["baro"].to_numpy()}
                 ).to_excel(baro_dir / "Patm Calès et Thémines.xlsx", index=False)

    # Points de controle du niveau : deux lectures sures sur la nouvelle echelle,
    # une lecture sur l'ancienne (doit etre refusee), une avec Correction = Non,
    # une hors tolerance horaire.
    pd.DataFrame({
        "Jour": ["03/04/2026 10:00", "06/12/2024 16:00", "12/05/2022 11:00",
                 "20/08/2023 09:00", "01/01/2018 10:00"],
        "Hauteur (cm)": [109.0, 107.0, 96.0, 101.0, 80.0],
        "Correction": ["Oui", "Non", "Oui", "Non", "Oui"],
    }).to_excel(base / "punctual_measurements.xlsx", index=False)

    pd.DataFrame({
        "Jour": ["03/04/2026 10:00", "12/05/2022 11:00"],
        "Conductivité": [455.0, 470.0],
        "Correction": ["Non", "Non"],
    }).to_excel(base / "punctual_measurements_conducti.xlsx", index=False)

    pluie = pd.DataFrame({"Date": pd.date_range(DEBUT, FIN, freq="1D")})
    pluie["Precipitation (mm)"] = np.clip(RNG.gamma(0.6, 4, len(pluie)) - 1, 0, None)
    pluie.to_csv(base / "Pluie_BV_Ouysse.csv", index=False)
    return base


def cellule_chemins(base):
    base = str(base)
    return f'''
import os
BASE = {base!r}
CTD_PATH    = os.path.join(BASE, "Données brutes", "CTD")
VUSITU_PATH = os.path.join(BASE, "Données brutes", "TROLL")
OTT_PATH    = os.path.join(BASE, "Données brutes", "OTT")
BARO_PATH   = os.path.join(BASE, "baro", "Patm Calès et Thémines.xlsx")
PLUIE_PATH  = os.path.join(BASE, "Pluie_BV_Ouysse.csv")
OLDDATA_PATH   = os.path.join(BASE, "Cabouy_consolide_OLD.xlsx")
UTC_CTD_PATH   = os.path.join(BASE, "UTC_CTD.xlsx")
UTC_TROLL_PATH = os.path.join(BASE, "UTC_Troll.xlsx")
PUNCTUAL_NIVEAU  = os.path.join(BASE, "punctual_measurements.xlsx")
PUNCTUAL_CONDUCT = os.path.join(BASE, "punctual_measurements_conducti.xlsx")
SORTIE_CONSOLIDE = os.path.join(BASE, "Cabouy_consolide.xlsx")
SORTIE_FINALE    = os.path.join(BASE, "Cabouy_final.xlsx")
SORTIE_SVG       = os.path.join(BASE, "Graphes.svg")
PREFIXE_CTD = "Cabouy"
BARO_COL    = "Patm Ouysse Calès [hPa]"
PAS         = "1h"
'''


def executer(notebook, base):
    nb = json.loads(Path(notebook).read_text(encoding="utf-8"))
    code = [("".join(c["source"])) for c in nb["cells"] if c["cell_type"] == "code"]
    code[1] = cellule_chemins(base)          # la 2e cellule de code porte les chemins

    espace = {"__name__": "__notebook__", "display": lambda *a, **k: None}
    import plotly.graph_objects as go
    go.Figure.show = lambda self, *a, **k: None
    for i, src in enumerate(code, start=1):
        try:
            exec(compile(src, f"<cellule {i}>", "exec"), espace)
        except Exception:
            print(f"\n=== ECHEC cellule de code {i} ===")
            raise
        print(f"--- cellule de code {i} OK ---")
    return espace


def verifier(espace, base):
    ok = True

    def check(nom, condition, detail=""):
        nonlocal ok
        ok = ok and bool(condition)
        print(f"  [{'OK ' if condition else 'KO '}] {nom}" + (f"  {detail}" if detail else ""))

    full = espace["full_data"]
    sondes = espace["SONDES"]

    check("3 conductivites distinctes", set(sondes["Conductivité"]) == {"OTT", "TROLL", "CTD"},
          str(sorted(sondes["Conductivité"])))
    check("3 temperatures distinctes", set(sondes["Température"]) == {"OTT", "TROLL", "CTD"})
    check("2 niveaux distincts", set(sondes["Niveau_(cm)"]) == {"OTT", "CTD"})
    check("TROLL direct et relais reunis en une sonde",
          "centrale" in sondes["Conductivité"]["TROLL"], sondes["Conductivité"]["TROLL"])

    chemins = espace["journal_chemins"]
    relais = chemins[chemins["chemin"].str.contains("TrollOTT", na=False)]
    ecarts_relais = relais["écart médian"].dropna().abs()
    check("aucun recalage entre les deux chemins du TROLL",
          (ecarts_relais < 0.5).all() if len(ecarts_relais) else True,
          f"ecart max {ecarts_relais.max():.3f}" if len(ecarts_relais) else "")
    combles = relais["n comblés"].sum()
    attendu_troll = int((TROU_TROLL[1] - TROU_TROLL[0]).total_seconds() // 3600) * 5
    check("le relais comble la panne du TROLL direct", combles == attendu_troll,
          f"{combles} pas comblés (attendu {attendu_troll})")

    # Grille horaire complete, sans ligne supprimee.
    attendu = pd.date_range(full.index.min(), full.index.max(), freq="1h")
    check("grille horaire reguliere et complete", full.index.equals(attendu),
          f"{len(full)} pas")

    # La campagne 4 doit avoir ete ignoree (metadonnee sans extension).
    ctd = espace["merge_ctd_df"]
    # La campagne 4 couvre 2025-09-25 -> 2026-04-30 : si elle avait ete lue, la
    # derniere date CTD serait en 2026. La campagne 3 s'arrete le 2025-09-30.
    check("campagne CTD mal nommee ignoree", ctd["DATE"].max() < pd.Timestamp("2025-10-01"),
          f"derniere date CTD {ctd['DATE'].max()}")

    # Compensation barometrique : le niveau CTD doit suivre la verite a une
    # constante pres, donc un ecart-type faible.
    ref = VERITE["niveau"].reindex(full.index)
    resid = (full["Niveau_CTD_(cm)"] - ref).dropna()
    check("niveau CTD = verite + constante", resid.std() < 1.5,
          f"ecart-type {resid.std():.3f} cm, moyenne {resid.mean():.2f} cm")
    check("compensation en cmH2O (pas en hPa)", abs(resid.std()) < 1.5)

    # Le recalage fige de la CTD sur l'OTT doit valoir exactement 76.86.
    fusion = espace["journal_fusion"]
    ligne = fusion[(fusion["paramètre"] == "Niveau_(cm)") & (fusion["sonde"] == "CTD")]
    check("decalage niveau CTD fige a 76.86", len(ligne) == 1
          and abs(ligne["décalage"].iloc[0] - 76.86) < 1e-9,
          str(ligne["origine"].tolist()))

    # Le point de controle sur l'ancienne echelle doit etre refuse, pas applique.
    jp = espace["journal_points_niveau"]
    refus = jp[jp["note"].str.startswith("non appliqué", na=False)]
    check("points de controle tous journalises", len(jp) == 5, f"{len(jp)} lignes")
    check("lecture sur l'ancienne echelle refusee",
          any("échelle" in str(n) for n in refus["note"]),
          "; ".join(sorted(set(refus["note"]))))
    applique = jp[jp["note"].str.startswith("calculé", na=False)]
    check("un seul point applique (03/04/2026)", len(applique) == 1,
          str(applique["date"].tolist()))

    # Apres calage, la serie doit passer par 109 cm le 03/04/2026 10:00.
    d = pd.Timestamp("2026-04-03 10:00")
    check("serie calee sur la lecture sure", abs(full.loc[d, "Niveau_(cm)"] - 109.0) < 1e-6,
          f"{full.loc[d, 'Niveau_(cm)']:.3f} cm")

    # Idempotence : relancer la cellule de correction du niveau donne le meme
    # resultat (elle repart de BRUT).
    avant = full["Niveau_(cm)"].copy()
    nb = json.loads(Path(sys.argv[1] if len(sys.argv) > 1
                         else "Cabouy_consolidation_V5.ipynb").read_text(encoding="utf-8"))
    code = [("".join(c["source"])) for c in nb["cells"] if c["cell_type"] == "code"]
    exec(compile(code[11], "<cellule 12 relancee>", "exec"), espace)
    apres = espace["full_data"]["Niveau_(cm)"]
    check("cellule niveau idempotente", avant.equals(apres))

    # Sens amont / aval.
    appliquer = espace["appliquer_recalage"]
    s = pd.Series(np.zeros(5), index=pd.date_range("2024-01-01", periods=5, freq="1D"))
    d = pd.Timestamp("2024-01-03")
    check("sens aval ne touche pas le passe",
          list(appliquer(s, d, 10, "aval")) == [0, 0, 10, 10, 10])
    check("sens amont ne touche pas le present",
          list(appliquer(s, d, 10, "amont")) == [10, 10, 0, 0, 0])
    check("sens tout deplace toute la serie",
          list(appliquer(s, d, 10, "tout")) == [10] * 5)

    # Tableaux de decision, affiches pour relecture.
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n--- journal_chemins ---");  print(chemins.to_string(index=False))
    print("\n--- couverture ---");       print(espace["couverture"].to_string(index=False))
    print("\n--- ecarts entre sondes ---"); print(espace["ecarts"].to_string(index=False))
    print("\n--- journal_fusion ---");   print(fusion.to_string(index=False))
    print("\n--- journal_points_niveau ---"); print(jp.to_string(index=False))
    print("\n--- repartition des sources ---")
    print(pd.DataFrame({p: full[f"{p}_source"].value_counts()
                        for p in espace["PARAMETRES"]}).fillna(0).astype(int).T.to_string())
    print()

    # Sorties ecrites.
    check("fichier final ecrit", (Path(base) / "Cabouy_final.xlsx").exists())
    check("fichier consolide ecrit", (Path(base) / "Cabouy_consolide.xlsx").exists())
    onglets = pd.ExcelFile(Path(base) / "Cabouy_final.xlsx").sheet_names
    check("journaux presents dans le fichier final",
          {"chronique", "fusion_sondes", "niveau_points_controle"} <= set(onglets),
          str(onglets))
    return ok


if __name__ == "__main__":
    notebook = sys.argv[1] if len(sys.argv) > 1 else "Cabouy_consolidation_V5.ipynb"
    base = Path(sys.argv[2] if len(sys.argv) > 2 else "jeu_de_test")
    base.mkdir(parents=True, exist_ok=True)
    print(f"Fabrication du jeu de test dans {base} ...")
    fabriquer(base)
    print("Execution du notebook ...\n")
    espace = executer(notebook, base)
    print("\nVerifications :")
    sys.exit(0 if verifier(espace, base) else 1)
