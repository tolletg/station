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
ECARTEE_NIVEAU = (pd.Timestamp("2019-10-14 17:00"), pd.Timestamp("2020-02-25 17:00"))


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

    check("calage CTD fige a +76.86 en amont",
          espace["CALAGE_CTD"] == ("2024-12-06 16:00", 76.86, "amont"),
          str(espace["CALAGE_CTD"]))

    # Le point de controle du 03/04/2026 est applique, les deux autres non.
    d = pd.Timestamp("2026-04-03 10:00")
    check("serie calee sur la lecture sure", abs(full.loc[d, "Niveau_(cm)"] - 109.0) < 1e-6,
          f"{full.loc[d, 'Niveau_(cm)']:.3f} cm")

    # La periode ecartee doit rester un trou jusque dans le fichier final.
    fenetre = full.loc[ECARTEE_NIVEAU[0]:ECARTEE_NIVEAU[1]]
    check("PERIODES_ECARTEES_NIVEAU laisse un vrai trou",
          fenetre["Niveau_(cm)"].isna().all()
          and (fenetre["Statut_Niveau_(cm)"] == "Manquante").all(),
          f"{len(fenetre)} pas, {int(fenetre['Niveau_(cm)'].notna().sum())} non-NaN")
    check("aucune ligne supprimee autour de la periode ecartee",
          len(fenetre) == int((ECARTEE_NIVEAU[1] - ECARTEE_NIVEAU[0]).total_seconds() // 3600) + 1)

    # Les voies ecartees au jugement le sont sur la VOIE, avant fusion.
    debut, fin, col, _ = espace["VOIES_ECARTEES"][0]
    check("voie ecartee avant fusion",
          brut.loc[pd.to_datetime(debut):pd.to_datetime(fin), col].isna().all(), col)

    # Idempotence : relancer la cellule du niveau redonne le meme resultat.
    avant = full["Niveau_(cm)"].copy()
    exec(compile(code[10], "<cellule niveau relancee>", "exec"), espace)
    check("cellule du niveau idempotente", avant.equals(espace["full_data"]["Niveau_(cm)"]))

    # Sens du decalage.
    decaler = espace["decaler"]
    s = pd.Series(np.zeros(5), index=pd.date_range("2024-01-01", periods=5, freq="1D"))
    d = pd.Timestamp("2024-01-03")
    check("sens aval ne touche pas le passe", list(decaler(s, d, 10, "aval")) == [0, 0, 10, 10, 10])
    check("sens amont ne touche pas le present", list(decaler(s, d, 10, "amont")) == [10, 10, 0, 0, 0])
    check("sens tout deplace toute la serie", list(decaler(s, d, 10, "tout")) == [10] * 5)

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
