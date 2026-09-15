"""Jeu de test synthetique pour les notebooks des stations autres que Cabouy.

Reprend le jeu de donnees de `jeu_de_test_cabouy` (memes pieges de format) et
l'adapte a chaque station : prefixe des campagnes CTD, presence ou non du
TROLL et de la centrale OTT, noms de colonnes de l'ancien consolide, fichiers
de points de controle. Execute toutes les cellules de code du notebook puis
verifie les proprietes communes au modele Cabouy.

    python3 tests/jeu_de_test_stations.py "Code pour ...-Fontbelle_V4.ipynb" /tmp/jdt
    python3 tests/jeu_de_test_stations.py --toutes /tmp/jdt
"""
import ast
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import jeu_de_test_cabouy as jt

COLONNES_OLD_CTD = {"Niveau_CTD_(cm)": "niveau", "Cond_CTD_(µS/cm)": "cond",
                    "Temp _CTD(°C)": "temp"}
COLONNES_OLD_TROLL = {"Cond_Troll_(µS/cm)": "cond", "température_Troll_(°C)": "temp",
                      "Turbidity_Troll_(NTU)": "turbi", "O2_Troll_(mg/l)": "o2",
                      "FluorescenceChloro_a_Troll_(RFU)": "chloro"}


def source(notebook):
    nb = json.loads(Path(notebook).read_text(encoding="utf-8"))
    return [("".join(c["source"])) for c in nb["cells"] if c["cell_type"] == "code"]


def config(code):
    """Lit dans le notebook ce dont le jeu de donnees a besoin."""
    espace = {"os": __import__("os")}
    exec(compile(code[1], "<chemins>", "exec"), espace)          # que des os.path.join
    renommage = {}
    for src in code:
        for noeud in ast.parse(src).body:
            if (isinstance(noeud, ast.Assign) and getattr(noeud.targets[0], "id", "")
                    == "RENOMMAGE_OLD"):
                renommage = ast.literal_eval(noeud.value)
    return espace, renommage


def base_de(chemin, base):
    """Dernier segment d'un chemin Windows ou POSIX."""
    return chemin[len(base):].strip("\\/").replace("\\", "/")


def fabriquer(dossier, ch, renommage, troll, ott):
    dossier = Path(dossier)
    for sous in ("CTD", "TROLL", "OTT", "baro"):
        (dossier / sous).mkdir(parents=True, exist_ok=True)

    sous = jt.VERITE.loc[jt.PERIODE_ANCIEN[0]:jt.PERIODE_ANCIEN[1]]
    ancien = pd.DataFrame({"DATE": sous.index})
    for col, cle in COLONNES_OLD_CTD.items():
        ancien[col] = sous[cle].to_numpy() + (jt.OFFSET_COND_CTD if cle == "cond" else
                                              jt.OFFSET_TEMP_CTD if cle == "temp" else 0.0)
    if troll:
        for col, cle in COLONNES_OLD_TROLL.items():
            ancien[col] = np.nan
    inverse = {v: k for k, v in renommage.items()}
    ancien = ancien.rename(columns=inverse)
    cible = dossier / base_de(ch["OLDDATA_PATH"], ch["BASE"])
    cible.parent.mkdir(parents=True, exist_ok=True)
    if cible.suffix.lower() == ".csv":
        a = ancien.copy()
        a["DATE"] = a["DATE"].dt.strftime("%d/%m/%Y %H:%M")
        a.to_csv(cible, sep=";", index=False)
    else:
        ancien.to_excel(cible, index=False)

    prefixe = ch["PREFIXE_CTD"]
    noms, fuseaux = [], []
    for i, (d, f, fuseau) in enumerate(jt.CAMPAGNES_CTD, start=1):
        nom = f"{prefixe}_{i}_diver.csv"
        jt.ecrire_ctd(dossier / "CTD" / nom, d, f, fuseau,
                      en_ms=(i == 2), encodage="cp1252" if i == 3 else "utf-8")
        noms.append(nom)
        fuseaux.append(fuseau)
    utc = dossier / base_de(ch["UTC_CTD_PATH"], ch["BASE"])
    utc.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Nom fichier": noms, "UTC Fichier": fuseaux}).to_excel(utc, index=False)

    if troll:
        noms, fuseaux = [], []
        for i, (d, f, fuseau) in enumerate(jt.FICHIERS_TROLL, start=1):
            nom = f"VuSitu_{i:02d}_export.csv"
            jt.ecrire_vusitu(dossier / "TROLL" / nom, d, f, fuseau, 736860 + 10 * i)
            noms.append(nom)
            fuseaux.append(fuseau)
        pd.DataFrame({"Nom fichier": noms, "UTC Fichier": fuseaux}).to_excel(
            dossier / base_de(ch["UTC_TROLL_PATH"], ch["BASE"]), index=False)
    if ott:
        jt.ecrire_ott(dossier / "OTT" / "OTT_export.csv", *jt.PERIODE_OTT)

    pd.DataFrame({"DATE": jt.VERITE.index,
                  "Patm Ouysse Calès [hPa]": jt.VERITE["baro"].to_numpy()}
                 ).to_excel(dossier / "baro" / "baro.xlsx", index=False)

    for nom, col, valeur in [(base_de(ch["PUNCTUAL_NIVEAU"], ch["BASE"]), "Hauteur (cm)", 109.0),
                             (base_de(ch["PUNCTUAL_CONDUCT"], ch["BASE"]), "Conductivité", 455.0)]:
        chemin = dossier / nom
        if chemin.exists():                       # un seul fichier pour les deux grandeurs
            df = pd.read_excel(chemin)
            df[col] = valeur
        else:
            df = pd.DataFrame({"Jour": ["03/04/2026 10:00"], col: [valeur],
                               "Correction": ["Oui" if col.startswith("Hauteur") else "Non"]})
        df.to_excel(chemin, index=False)

    pluie = pd.DataFrame({"Date": pd.date_range(jt.DEBUT, jt.FIN, freq="1D")})
    pluie["Precipitation (mm)"] = np.clip(jt.RNG.gamma(0.6, 4, len(pluie)) - 1, 0, None)
    pluie.to_csv(dossier / "Pluie_BV_Ouysse.csv", index=False)


def cellule_chemins(dossier, ch, troll, ott):
    d = Path(dossier)
    lignes = [f"import os", f"BASE = {str(d)!r}",
              f'CTD_PATH = os.path.join(BASE, "CTD")',
              f'BARO_PATH = os.path.join(BASE, "baro", "baro.xlsx")',
              f'PLUIE_PATH = os.path.join(BASE, "Pluie_BV_Ouysse.csv")',
              f'BARO_COL = "Patm Ouysse Calès [hPa]"', 'PAS = "1h"',
              f'PREFIXE_CTD = {ch["PREFIXE_CTD"]!r}']
    if troll:
        lignes += ['VUSITU_PATH = os.path.join(BASE, "TROLL")',
                   f'UTC_TROLL_PATH = os.path.join(BASE, {base_de(ch["UTC_TROLL_PATH"], ch["BASE"])!r})']
    if ott:
        lignes.append('OTT_PATH = os.path.join(BASE, "OTT")')
    for var in ("OLDDATA_PATH", "UTC_CTD_PATH", "PUNCTUAL_NIVEAU", "PUNCTUAL_CONDUCT",
                "SORTIE_CONSOLIDE", "SORTIE_FINALE", "SORTIE_SVG"):
        lignes.append(f'{var} = os.path.join(BASE, {base_de(ch[var], ch["BASE"])!r})')
    return "\n".join(lignes)


def executer(code, dossier, ch, troll, ott):
    code = list(code)
    code[1] = cellule_chemins(dossier, ch, troll, ott)
    import plotly.graph_objects as go
    go.Figure.show = lambda self, *a, **k: None
    espace = {"__name__": "__notebook__", "display": lambda *a, **k: None}
    for i, src in enumerate(code, start=1):
        try:
            exec(compile(src, f"<cellule {i}>", "exec"), espace)
        except Exception:
            print(f"\n=== ECHEC cellule de code {i} ===")
            raise
    return espace


def verifier(nom, espace, dossier, ch):
    ok = [True]

    def check(titre, condition, detail=""):
        ok[0] &= bool(condition)
        print(f"  [{'OK ' if condition else 'KO '}] {titre}" + (f"  {detail}" if detail else ""))

    full = espace["full_data"]
    attendu = pd.date_range(full.index.min(), full.index.max(), freq="1h")
    check("grille horaire reguliere", full.index.equals(attendu), f"{len(full)} pas")

    for p in espace["PARAMETRES"]:
        check(f"chronique non vide : {p}", full[p].notna().sum() > 1000,
              f"{int(full[p].notna().sum())} pas")
        check(f"statut renseigne : {p}", full[f"Statut_{p}"].isin(
            ["Mesurée", "Interpolée", "Manquante"]).all())

    # Les voies ecartees sont bien des trous dans CORRIGE, pas dans BRUT.
    for debut, fin, col, _ in espace["VOIES_ECARTEES"]:
        d, f = sorted([pd.to_datetime(debut), pd.to_datetime(fin)])
        if f < full.index.min() or d > full.index.max():
            continue
        check(f"voie ecartee : {col} {d:%d/%m/%Y}",
              espace["CORRIGE"].loc[d:f, col].isna().all())

    # Le choix automatique suit ORDRE : la sonde de tete gagne quand elle mesure.
    voies = espace["voies_calees"]("Conductivité")
    blocs = espace["choisir_sondes"](voies, espace["ORDRE"])
    tete = espace["ORDRE"][0]
    if tete in voies and voies[tete].notna().any():
        choix = pd.Series(pd.NA, index=voies[tete].index, dtype="object")
        for d, f, s in blocs:
            choix.loc[d:f] = s
        mesure = voies[tete].notna().to_numpy()
        pris = int((choix.eq(tete).fillna(False).to_numpy() & mesure).sum())
        check("ordre automatique respecte", pris > 0.9 * mesure.sum(),
              f"{pris} / {int(mesure.sum())} pas a la sonde de tete")

    # Cote NGF : formule directe, plus celle de l'ancienne version.
    if espace.get("NIVEAU_NGF") is not None:
        ngf, h = espace["NIVEAU_NGF"], full["Niveau_(cm)"]
        check("cote NGF = zero + h / 100",
              float((full["Niveau_(mNGF)"] - (ngf + h / 100)).abs().max()) < 1e-9,
              f"zero a {ngf:.4f} m NGF")

    # Debit : positif, et conforme a la courbe de tarage sur le niveau interpole.
    col_q = next((c for c in full.columns if c.startswith("Q_(")), None)
    if col_q:
        q = full[col_q].dropna()
        check("debit jamais negatif", (q >= 0).all(), f"min {q.min():.3f}")
        recalcule = espace["debit"](full["Niveau_(cm)"])
        check("debit recalcule sur le niveau interpole",
              float((full[col_q] - recalcule).abs().max()) < 1e-9)

    # Filtre IQR : n'ajoute jamais de valeur, et n'agit pas si K_IQR vaut 0.
    if "cond_iqr" in espace:
        avant, apres = espace["cond"].notna().sum(), espace["cond_iqr"].notna().sum()
        if espace["K_IQR"]:
            check("filtre IQR : des valeurs ecartees", apres <= avant, f"{avant} vers {apres}")
        else:
            check("filtre IQR desactive : chronique inchangee", apres == avant)

    # Fichier final : une valeur et un statut par grandeur, pas de colonne source.
    final = pd.read_excel(ch["SORTIE_FINALE"].replace(ch["BASE"], str(dossier)))
    check("fichier final ecrit", len(final) == len(full), f"{len(final)} lignes")
    check("fichier final sans colonne source",
          not any(c.endswith("_source") for c in final.columns))
    check("fichier final : un statut par grandeur",
          all(f"Statut_{p}" in final.columns for p in espace["PARAMETRES"]))
    return ok[0]


def lancer(notebook, dossier):
    print(f"\n=== {Path(notebook).name}")
    code = source(notebook)
    ch, renommage = config(code)
    troll, ott = "VUSITU_PATH" in ch, "OTT_PATH" in ch
    dossier = Path(dossier) / Path(notebook).stem.replace(" ", "_")
    dossier.mkdir(parents=True, exist_ok=True)
    fabriquer(dossier, ch, renommage, troll, ott)
    espace = executer(code, dossier, ch, troll, ott)
    print(f"  {len(code)} cellules de code executees sans erreur.")
    return verifier(Path(notebook).name, espace, dossier, ch)


if __name__ == "__main__":
    args = sys.argv[1:]
    dossier = args[-1]
    if args[0] == "--toutes":
        cibles = sorted(str(p) for p in Path(".").glob("Code pour consolider les données-*.ipynb")
                        if any(s in p.name for s in ("Fontbelle_V4", "Saint_Sauveur_V3",
                                                     "Thémines_V2", "Ouysse_V3")))
    else:
        cibles = args[:-1]
    sys.exit(0 if all([lancer(c, dossier) for c in cibles]) else 1)
