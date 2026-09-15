# -*- coding: utf-8 -*-
"""Genere les notebooks des stations sur le modele de Cabouy.

Le notebook de Cabouy est le gabarit : ses fonctions de lecture et de
correction sont recopiees telles quelles, les blocs des sondes absentes sont
retires, et `stations.py` fournit les chemins, les priorites et les corrections
propres a chaque station. Relancer apres toute evolution de Cabouy :

    python3 tests/generer_stations.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stations import STATIONS, BARO, PLUIE

REPO = Path(__file__).resolve().parent.parent
GABARIT = REPO / "Code pour consolider les données-Cabouy_V4.ipynb"

gab = json.loads(GABARIT.read_text(encoding="utf-8"))
G = ["".join(c["source"]) for c in gab["cells"]]
IMPORTS, LECTURE, CORRECTION = G[2], G[6], G[8]
CELL_CTD, CELL_TROLL, CELL_OTT = G[10], G[14], G[16]


def sans_blocs(source, motifs):
    """Retire les blocs de premier niveau qui contiennent un des motifs."""
    blocs = source.split("\n\n\n")
    return "\n\n\n".join(b for b in blocs if not any(m in b for m in motifs))


OTT_SEUL = '''#: Voies de la centrale : level, C1, T1 viennent de SA sonde CTD.
NOMS_OTT = {"level": "Niveau_CTDOTT_(cm)",
            "c1": "Cond_CTDOTT_(µS/cm)", "t1": "Temp_CTDOTT_(°C)"}'''


def remplacer_bloc(source, motif, nouveau):
    """Remplace le bloc de premier niveau qui contient `motif`."""
    blocs = [nouveau if motif in b else b for b in source.split("\n\n\n")]
    return "\n\n\n".join(blocs)


def table_sondes(st):
    """Texte du dict SONDES et liste des grandeurs, selon les sondes presentes."""
    d = {"Niveau_(cm)": [("CTD", "Niveau_CTD_(cm)")],
         "Conductivité": [("CTD", "Cond_CTD_(µS/cm)")],
         "Température": [("CTD", "Temp _CTD(°C)")]}
    if st["troll"]:
        d["Conductivité"].insert(0, ("TROLL", "Cond_Troll_(µS/cm)"))
        d["Température"].insert(0, ("TROLL", "température_Troll_(°C)"))
        d["Turbidité_(NTU)"] = [("TROLL", "Turbidity_Troll_(NTU)")]
        d["O2_(mg/l)"] = [("TROLL", "O2_Troll_(mg/l)")]
        d["Chlorophylle_(RFU)"] = [("TROLL", "FluorescenceChloro_a_Troll_(RFU)")]
    if st["ott"]:
        d["Niveau_(cm)"].insert(0, ("OTT", "Niveau_CTDOTT_(cm)"))
        d["Conductivité"].insert(-1, ("OTT", "Cond_CTDOTT_(µS/cm)"))
        d["Température"].insert(-1, ("OTT", "Temp_CTDOTT_(°C)"))
    grandeurs = [g for g in ["Niveau_(cm)", "Conductivité", "Température", "Turbidité_(NTU)",
                             "O2_(mg/l)", "Chlorophylle_(RFU)"] if g in d]
    lignes = []
    for g in grandeurs:
        courant = ('    "%s":' % g).ljust(26) + "{"
        for i, (sonde, col) in enumerate(d[g]):
            paire = '"%s": "%s"' % (sonde, col) + ("," if i < len(d[g]) - 1 else "},")
            if len(courant) + len(paire) > 96:
                lignes.append(courant.rstrip())
                courant = " " * 27
            courant += paire + (" " if not paire.endswith("},") else "")
        lignes.append(courant.rstrip())
    return "\n".join(lignes), grandeurs


def liste_py(entrees, indent=4):
    """Une entree de tuple par ligne, comme dans le notebook de Cabouy."""
    pad = " " * indent
    return "\n".join(pad + "(" + ", ".join('"%s"' % v if isinstance(v, str) else repr(v)
                                           for v in e) + ")," for e in entrees)


def md(txt):
    return {"cell_type": "markdown", "metadata": {}, "source": txt.strip("\n").splitlines(keepends=True)}


def code(txt):
    return {"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None,
            "source": txt.strip("\n").splitlines(keepends=True)}


CHEMINS = '''
BASE        = r"__BASE__"
CTD_PATH    = os.path.join(BASE, r"Données brutes\\CTD")
__VUSITU____OTT__BARO_PATH   = r"__BARO__"
PLUIE_PATH  = r"__PLUIE__"

OLDDATA_PATH     = os.path.join(BASE, "__OLD__")
UTC_CTD_PATH     = os.path.join(BASE, r"__UTC_CTD__")
__UTC_TROLL__PUNCTUAL_NIVEAU  = os.path.join(BASE, "__PUNCT_N__")
PUNCTUAL_CONDUCT = os.path.join(BASE, "__PUNCT_C__")
SORTIE_CONSOLIDE = os.path.join(BASE, "__CONSOLIDE__")
SORTIE_FINALE    = os.path.join(BASE, "__FINALE__")
SORTIE_SVG       = os.path.join(BASE, "Graphes.svg")

PREFIXE_CTD = "__PREFIXE__"
BARO_COL    = "Patm Ouysse Calès [hPa]"
PAS         = "1h"
'''

RACCORD = '''
#: L'ancien consolidé n'emploie pas toujours les noms de colonnes du notebook.
RENOMMAGE_OLD = {
__RENOMMAGE__
}

olddata_df = __LECTURE_OLD__
olddata_df["DATE"] = pd.to_datetime(olddata_df["DATE"], errors="coerce"__DAYFIRST__)
olddata_df = (olddata_df.rename(columns=RENOMMAGE_OLD).dropna(subset=["DATE"])
              .sort_values("DATE"))

ancien, nouveau = olddata_df.set_index("DATE"), merge_ctd_df.set_index("DATE")
grandeurs = [("Niveau", "Niveau_CTD_(cm)", "Niveau_(cm)", "cm"),
             ("Conductivité", "Cond_CTD_(µS/cm)", "Cond_(µS/cm)", "µS/cm")]
for nom, col_a, col_n, unite in grandeurs:
    a, n = ancien[col_a].dropna(), nouveau[col_n].dropna()
    d = float(a.iloc[-1] - n.iloc[0]) if len(a) and len(n) else 0.0
    print(f"{nom:13s} : {d:+9.2f} {unite:6s} mesuré à la jonction  "
          f"{a.index[-1]:%d/%m/%Y %H:%M} vers {n.index[0]:%d/%m/%Y %H:%M}")
    merge_ctd_df[col_n] = merge_ctd_df[col_n] + d

bord = olddata_df["DATE"].max()
fig, axes = plt.subplots(2, 1, figsize=(8, 3), sharex=True)
for ax, (nom, col_a, col_n, unite) in zip(axes, grandeurs):
    ax.plot(olddata_df["DATE"], olddata_df[col_a], color="green", label="ancienne chronique")
    ax.plot(merge_ctd_df["DATE"], merge_ctd_df[col_n], color="blue", label="campagnes raccordées")
    ax.set_ylabel(f"{nom} ({unite})")
    ax.legend(loc="upper left")
axes[0].set_xlim(bord - pd.Timedelta(days=7), bord + pd.Timedelta(days=7))
plt.tight_layout()
plt.show()
'''

ASSEMBLAGE = '''
COLONNES_CTD   = ["Niveau_CTD_(cm)", "Cond_CTD_(µS/cm)", "Temp _CTD(°C)"]
__COLONNES_TROLL____DOUBLONS__

def empiler(morceaux, colonnes):
    pile = pd.concat(morceaux, ignore_index=True).dropna(subset=["DATE"])
    pile = pile[["DATE"] + [c for c in colonnes if c in pile.columns]]
    return (pile.sort_values("DATE", kind="stable")
            .drop_duplicates("DATE", keep="first").set_index("DATE"))


piles = [
    empiler([olddata_df,
             merge_ctd_df.rename(columns={"Niveau_(cm)": "Niveau_CTD_(cm)",
                                          "Cond_(µS/cm)": "Cond_CTD_(µS/cm)",
                                          "Temp_(°C)": "Temp _CTD(°C)"})], COLONNES_CTD),
__PILES__]

grille = pd.date_range(min(p.index.min() for p in piles),
                       max(p.index.max() for p in piles), freq=PAS, name="DATE")
full_data = pd.DataFrame(index=grille)
for pile in piles:
    for col in pile.columns:
        full_data[col] = pile[col].reindex(grille)
print(f"{len(full_data)} pas horaires, du {grille.min():%d/%m/%Y} au {grille.max():%d/%m/%Y}")

print("Hors gamme physique :")
full_data = appliquer_gammes(full_data)
__RELAIS__
#: Les sondes de chaque grandeur : {grandeur: {sonde: colonne}}.
SONDES = {
__SONDES__
}
PARAMETRES = list(SONDES)

#: Ordre de préférence automatique : à chaque pas, la première sonde qui mesure.
ORDRE = __ORDRE__

BRUT = full_data.copy()
full_data.to_excel(SORTIE_CONSOLIDE)
print(f"\\nfichier fusionné : {SORTIE_CONSOLIDE}")
'''

RELAIS = '''
print("Trous du TROLL direct comblés par la centrale :")
for direct, relais in DOUBLONS:
    trou = (full_data[direct].isna() & full_data[relais].notna()).to_numpy()
    full_data[direct] = full_data[direct].where(~trou, full_data[relais])
    print(f"  {direct:34s} {int(trou.sum()):6d} pas")
'''

CORRECTIONS = '''
#: (début, fin, colonne, motif) : mesures mises à l'écart, toutes grandeurs.
VOIES_ECARTEES = [
__ECARTEES__
]

#: (date d'ancrage, sonde, grandeur, décalage, sens) : ajustements manuels.
#: sens = "amont" (avant la date) | "aval" (à partir de la date) | "tout".
CALAGES_SONDE = [
__CALAGES__
]
print("Voies écartées :")
CORRIGE = ecarter(BRUT.copy(), VOIES_ECARTEES)

def voies_calees(grandeur):
    """Les séries des sondes d'une grandeur, écarts et calages appliqués."""
    series = {s: CORRIGE[c] for s, c in SONDES[grandeur].items()}
    for date, sonde, cible, valeur, sens in CALAGES_SONDE:
        if cible == grandeur and sonde in series:
            series[sonde] = decaler(series[sonde], date, valeur, sens)
            print(f"  {sonde} : {valeur:+.2f} en {sens} du "
                  f"{pd.to_datetime(date):%d/%m/%Y %H:%M}")
    return series
'''

COMPARAISON = '''
PARAMETRE = "Conductivité"   # __GRANDEURS__

graphe([(BRUT[col], f"sonde {sonde}", COULEURS[sonde])
        for sonde, col in SONDES[PARAMETRE].items()],
       titre=f"{PARAMETRE} : les sondes disponibles", ylab=PARAMETRE)
'''

NIVEAU = '''
#: (début, fin, sonde imposée) : sort du choix automatique sur cette période.
SONDE_PRIORITAIRE_NIVEAU = [
__PRIO_NIVEAU__
]
points_niveau = pd.read_excel(PUNCTUAL_NIVEAU)
points_niveau["Datetime"] = pd.to_datetime(points_niveau["Jour"], dayfirst=True, errors="coerce")

print("Calages de sonde :")
voies = voies_calees("Niveau_(cm)")
print("Périodes retenues :")
avant, source = fusionner(voies, choisir_sondes(voies, ORDRE, SONDE_PRIORITAIRE_NIVEAU), "cm")

print("Points de contrôle :")
niveau = caler(avant, points_niveau, "Hauteur (cm)")
full_data["Niveau_(cm)"], full_data["Niveau_(cm)_source"] = niveau, source
print("Pas de temps par sonde :", source.value_counts().to_dict())

graphe([(serie, f"sonde {sonde}", COULEURS[sonde]) for sonde, serie in voies.items()]
       + [(avant, "fusion, avant correction", "lightgrey"),
          (niveau, "chronique corrigée", "black")],
       titre="Niveau", ylab="Niveau (cm)", points=points_niveau, col_point="Hauteur (cm)")
'''

CONDUCTIVITE = '''
#: (début, fin, sonde imposée) : sort du choix automatique sur cette période.
SONDE_PRIORITAIRE_COND = [
__PRIO_COND__
]
points_cond = pd.read_excel(PUNCTUAL_CONDUCT)
points_cond["Datetime"] = pd.to_datetime(points_cond["Jour"], dayfirst=True, errors="coerce")

print("Calages de sonde :")
voies = voies_calees("Conductivité")
print("Périodes retenues :")
avant, source = fusionner(voies, choisir_sondes(voies, ORDRE, SONDE_PRIORITAIRE_COND), "µS/cm")

print("Points de contrôle :")
cond = caler(avant, points_cond, "Conductivité")
print("Pas de temps par sonde :", source.value_counts().to_dict())

graphe([(serie, f"sonde {sonde}", COULEURS[sonde]) for sonde, serie in voies.items()]
       + [(avant, "fusion, avant correction", "lightgrey"),
          (cond, "chronique fusionnée et calée", "black")],
       titre="Conductivité", ylab="Conductivité (µS/cm)",
       points=points_cond, col_point="Conductivité")
'''

IQR = '''
FENETRE_IQR, K_IQR = "__FENETRE__", __K__   # k = 0 : pas de filtre
LISSAGE_H = __LISSAGE__                     # 0 = pas de lissage ; sinon médiane glissante, en heures

hors = pd.Series(False, index=cond.index)
if K_IQR:
    r = cond.rolling(FENETRE_IQR, center=True, min_periods=8)
    q1, q3 = r.quantile(0.25), r.quantile(0.75)
    hors = ((cond < q1 - K_IQR * (q3 - q1)) | (cond > q3 + K_IQR * (q3 - q1))).fillna(False)
cond_iqr = cond.mask(hors)
print(f"Filtre IQR ({FENETRE_IQR}, k={K_IQR}) : {int(hors.sum())} valeurs écartées")

if LISSAGE_H:
    cond_iqr = cond_iqr.rolling(f"{LISSAGE_H}h", center=True, min_periods=1).median()
    print(f"Lissage : médiane glissante sur {LISSAGE_H} h")

full_data["Conductivité"], full_data["Conductivité_source"] = cond_iqr, source
full_data["Conductivité_Moyenne_Mobile"] = cond_iqr.rolling("6h", center=True).mean()

graphe([(cond, "avant IQR et lissage", "darkorange"),
        (cond_iqr, "après IQR et lissage", "black")],
       titre="Conductivité", ylab="Conductivité (µS/cm)")
'''

AUTRES = '''
#: {grandeur: [(début, fin, sonde imposée)]} pour sortir du choix automatique.
EXCEPTIONS = {}

for grandeur in __AUTRES__:
    print(f"{grandeur} :")
    voies = voies_calees(grandeur)
    full_data[grandeur], full_data[f"{grandeur}_source"] = fusionner(
        voies, choisir_sondes(voies, ORDRE, EXCEPTIONS.get(grandeur, [])))
    print(f"  {full_data[grandeur].notna().sum()} pas  "
          f"{full_data[f'{grandeur}_source'].value_counts().to_dict()}")
'''

DEBIT = '''
SEUIL_H = __SEUIL__     # cm, raccord des deux branches de la courbe de tarage

def debit(H):
    """Débit en __UNITE__ à partir du niveau en cm, jamais négatif."""
    h = pd.to_numeric(H, errors="coerce").astype("float64")
__CORPS__
    return pd.Series(np.where(h.isna(), np.nan, np.maximum(Q, 0.0)), index=H.index)

full_data["Q_(__UNITE__)"] = debit(full_data["Niveau_(cm)"])
display(full_data[["Niveau_(cm)", "Q_(__UNITE__)"]].describe().round(3))
'''

STATUTS = '''
NIVEAU_NGF = __NGF__       # cote du zéro de l'échelle, None si elle n'est pas connue
MAX_TROU_H = 12

max_pas = int(pd.Timedelta(f"{MAX_TROU_H}h") / pd.Timedelta(PAS))
for col in PARAMETRES:
    origine = full_data[col]
    manquant = origine.isna().to_numpy()
    groupe = np.cumsum(np.r_[True, manquant[1:] != manquant[:-1]])
    tailles = pd.Series(groupe).groupby(groupe).transform("size").to_numpy()
    comble = origine.interpolate(method="time", limit_direction="both")
    comble = comble.mask(manquant & (tailles > max_pas))
    mesures = np.flatnonzero(~manquant)          # pas d'extrapolation hors plage mesurée
    if mesures.size:
        comble.iloc[:mesures[0]] = origine.iloc[:mesures[0]]
        comble.iloc[mesures[-1] + 1:] = origine.iloc[mesures[-1] + 1:]
    full_data[col] = comble
    full_data[f"Statut_{col}"] = np.where(
        ~manquant, "Mesurée", np.where(comble.notna().to_numpy(), "Interpolée", "Manquante"))

if NIVEAU_NGF is not None:
    full_data["Niveau_(mNGF)"] = NIVEAU_NGF + full_data["Niveau_(cm)"] / 100
    full_data["Statut_Niveau_(mNGF)"] = full_data["Statut_Niveau_(cm)"]
    print(f"Zéro de l'échelle à {NIVEAU_NGF:.4f} m NGF")
__RECALCUL_Q__display(pd.DataFrame({c: full_data[f"Statut_{c}"].value_counts()
                      for c in PARAMETRES}).fillna(0).astype(int).T)
'''

RECALCUL_Q = '''
full_data["Q_(__UNITE__)"] = debit(full_data["Niveau_(cm)"])   # sur le niveau interpolé
full_data["Statut_Q_(__UNITE__)"] = full_data["Statut_Niveau_(cm)"]

'''

SAUVEGARDE = '''
finaux = [c for c in PARAMETRES + ["Q_(__UNITE__)", "Niveau_(mNGF)"] if c in full_data]
colonnes = [c for p in finaux for c in (p, f"Statut_{p}") if c in full_data]
full_data[colonnes].to_excel(SORTIE_FINALE)
print(f"{SORTIE_FINALE} : {len(full_data)} pas x {len(colonnes)} colonnes")

fig, axes = plt.subplots(__N_PANNEAUX__, 1, figsize=(15, __HAUTEUR__), sharex=True,
                         gridspec_kw={"hspace": 0.05})
__PANNEAU0__
axes[1].plot(full_data.index, full_data["Conductivité_Moyenne_Mobile"], color="black")
axes[1].set_ylabel("Conductivité (µS/cm)")
ax = axes[1].twinx()
ax.plot(full_data.index, full_data["Température"].rolling(12, center=True).mean(), color="crimson")
ax.set_ylabel("Température (°C)", color="crimson")
__PANNEAU2__
plt.savefig(SORTIE_SVG, format="svg")
plt.show()
'''

PANNEAU0 = '''
axes[0].plot(full_data.index, full_data[__COURBE0__].rolling(12, center=True).mean(),
             color="lightseagreen")
axes[0].set_ylabel("__LABEL0__", color="lightseagreen")
if os.path.exists(PLUIE_PATH):
    pluie = pd.read_csv(PLUIE_PATH)
    ax = axes[0].twinx()
    ax.bar(pd.to_datetime(pluie["Date"], errors="coerce"), pluie["Precipitation (mm)"],
           width=0.8, color="royalblue")
    ax.invert_yaxis()
    ax.set_ylabel("Précipitations (mm)", color="royalblue")
'''

PANNEAU2 = '''
axes[2].plot(full_data.index, full_data["Turbidité_(NTU)"].rolling(24, center=True).mean(),
             color="darkorange")
axes[2].set_ylabel("Turbidité (NTU)", color="darkorange")
axes[2].set_ylim(0, 100)
ax = axes[2].twinx()
ax.plot(full_data.index, full_data["O2_(mg/l)"].rolling(24, center=True).mean(),
        color="darkmagenta")
ax.set_ylabel("Oxygène (mg/L)", color="darkmagenta")
ax = axes[2].twinx()
ax.spines["right"].set_position(("outward", 45))
ax.plot(full_data.index, full_data["Chlorophylle_(RFU)"].rolling(24, center=True).mean(),
        color="green")
ax.set_ylabel("Chlorophylle (RFU)", color="green")
'''

INTERPOLATION = '''
fig = go.Figure()
for p in finaux:
    for nom, couleur in [("Mesurée", "black"), ("Interpolée", "crimson")]:
        m = (full_data[f"Statut_{p}"] == nom).to_numpy()
        fig.add_trace(go.Scattergl(x=full_data.index[m], y=full_data[p][m], mode="markers",
                                   name=nom, marker=dict(color=couleur, size=3),
                                   visible=(p == finaux[0])))
fig.update_layout(
    updatemenus=[dict(buttons=[dict(label=p, method="update",
                                    args=[{"visible": [q == p for q in finaux for _ in (0, 1)]},
                                          {"yaxis.title.text": p}])
                               for p in finaux],
                      x=0, xanchor="left", y=1.18)],
    title="Statut des données", xaxis_title="Date", yaxis_title=finaux[0],
    template="plotly_white", hovermode="x unified")
fig.show()

print(pd.DataFrame({p: full_data[f"Statut_{p}"].value_counts() for p in finaux})
      .fillna(0).astype(int).T.to_string())
'''


def remplir(gab, **kw):
    for cle, val in kw.items():
        gab = gab.replace("__%s__" % cle, str(val))
    return gab


def construire(nom, st):
    sondes_txt, grandeurs = table_sondes(st)
    cellules, n = [], [0]

    def titre(t):
        n[0] += 1
        return "## %d. %s" % (n[0], t)

    presentes = ["**CTD** (Diver autonome : niveau, conductivité, température)"]
    if st["troll"]:
        presentes.append("**TROLL** (Aqua TROLL : conductivité, température, turbidité, "
                         "O2, chlorophylle)")
    if st["ott"]:
        presentes.append("**OTT** (sonde CTD de la centrale : niveau, conductivité, température)")
    entete_ott = st["ott"] and st["troll"]
    entete = ("# %s - consolidation des chroniques\n\n%s sonde%s : %s.\n"
              % (st["titre"], {1: "Une", 2: "Deux", 3: "Trois"}[len(presentes)],
                 "s" if len(presentes) > 1 else "", ", ".join(presentes)))
    if entete_ott:
        entete += ("\nLa centrale rapatrie aussi les voies du TROLL (`C2`, `T2`, `Turbi`, `O2`,\n"
                   "`Chlorophyl`) : c'est le même capteur que les exports VuSitu, un second chemin\n"
                   "d'acquisition, pas une quatrième sonde. Les deux sont réunis à l'assemblage,\n"
                   "sans recalage.\n")
    entete += ("\nMême logique qu'à Cabouy, la station de référence : une colonne par sonde, une\n"
               "sonde choisie automatiquement à chaque pas dans l'ordre `ORDRE`, des périodes\n"
               "imposées à la main quand le graphe montre que ce choix n'est pas le bon, et un\n"
               "recalage mesuré à chaque changement de sonde.\n")
    cellules.append(md(entete))

    cellules += [md(titre("Imports")), code(IMPORTS)]

    vusitu = 'VUSITU_PATH = os.path.join(BASE, r"Données brutes\\TROLL")\n' if st["troll"] else ""
    ott = 'OTT_PATH    = os.path.join(BASE, r"Données brutes\\OTT")\n' if st["ott"] else ""
    utc_troll = 'UTC_TROLL_PATH   = os.path.join(BASE, "UTC_Troll.xlsx")\n' if st["troll"] else ""
    cellules += [md(titre("Chemins d'accès")),
                 code(remplir(CHEMINS, BASE=st["base"], VUSITU=vusitu, OTT=ott, BARO=BARO,
                              PLUIE=PLUIE, OLD=st["olddata"],
                              UTC_CTD=st.get("utc_ctd", "UTC_CTD.xlsx"), UTC_TROLL=utc_troll,
                              PUNCT_N=st["punctual_niveau"], PUNCT_C=st["punctual_cond"],
                              CONSOLIDE=st["sortie_consolide"], FINALE=st["sortie_finale"],
                              PREFIXE=st["prefixe"]))]

    retire = []
    if not st["troll"]:
        retire += ["NOMS_TROLL = {", "def lire_VuSitu"]
    if not st["ott"]:
        retire += ["NOMS_OTT = {", "def lire_OTT"]
    lecture = sans_blocs(LECTURE, retire)
    if st["ott"] and not st["troll"]:      # la centrale ne rapatrie aucune voie TROLL
        lecture = remplacer_bloc(lecture, "NOMS_OTT = {", OTT_SEUL)
    cellules += [md(titre("Fonctions de lecture") + """

Les pièges de format : en-tête Diver à une ligne variable et pied `END OF DATA`,
virgules décimales, conductivité en mS/cm ou µS/cm selon la campagne, encodages
mélangés. La table UTC nomme les fichiers exactement, sinon la campagne est ignorée."""),
                 code(lecture),
                 md("""### Fonctions de correction

`decaler` porte le choix du sens : `aval` pour une marche réelle (capteur déplacé),
`amont` pour ramener l'historique sur la référence actuelle, `tout` pour un calage
d'appareil. `raccorder` mesure le décalage **à la jonction**, `choisir_sondes` découpe
la chronique en périodes et `fusionner` les enchaîne en recalant chaque changement."""),
                 code(CORRECTION)]

    cellules += [md(titre("CTD : lecture, UTC et compensation barométrique")), code(CELL_CTD)]

    lecture_old = ('pd.read_csv(OLDDATA_PATH, sep=";")' if st["old_csv"]
                   else "pd.read_excel(OLDDATA_PATH)")
    renom = "\n".join('    "%s": "%s",' % (a, b) for a, b in st["renommage_old"].items())
    cellules += [md(titre("Raccordement à l'ancienne chronique") + """

L'ancien fichier consolidé et les campagnes récentes sont la **même sonde CTD**, séparées
par un trou d'exploitation : le décalage est mesuré à la jonction et appliqué aux
campagnes, pour que la chronique soit continue."""),
                 code(remplir(RACCORD, RENOMMAGE=renom, LECTURE_OLD=lecture_old,
                              DAYFIRST=", dayfirst=True" if st["old_csv"] else ""))]

    if st["troll"]:
        cellules += [md(titre("TROLL : exports VuSitu")), code(CELL_TROLL)]
    if st["ott"]:
        cellules += [md(titre("Centrale OTT")), code(CELL_OTT)]

    col_troll = ""
    piles, relais, doublons = "", "", ""
    if st["troll"]:
        col_troll = ('COLONNES_TROLL = ["Cond_Troll_(µS/cm)", "température_Troll_(°C)", '
                     '"Turbidity_Troll_(NTU)",\n'
                     '                  "O2_Troll_(mg/l)", "O2 (%Sat)", '
                     '"FluorescenceChloro_a_Troll_(RFU)",\n'
                     '                  "ConcentrationChloro_a_(µg/l)"]\n')
        piles += "    empiler([olddata_df, merge_troll_df], COLONNES_TROLL),\n"
    if st["ott"] and st["troll"]:
        doublons = ('#: (voie directe, même voie rapatriée par la centrale)\n'
                    'DOUBLONS = [("Cond_Troll_(µS/cm)", "Cond_TrollOTT_(µS/cm)"),\n'
                    '            ("température_Troll_(°C)", "Temp_TrollOTT_(°C)"),\n'
                    '            ("Turbidity_Troll_(NTU)", "Turbidity_TrollOTT_(NTU)"),\n'
                    '            ("O2_Troll_(mg/l)", "O2_TrollOTT_(mg/l)"),\n'
                    '            ("FluorescenceChloro_a_Troll_(RFU)",\n'
                    '             "FluorescenceChloro_a_TrollOTT_(RFU)")]\n')
        relais = RELAIS
    if st["ott"]:
        piles += "    empiler([merge_ott_df], list(NOMS_OTT.values())),\n"
    md_assemblage = titre("Assemblage : une colonne par sonde")
    if st["ott"] and st["troll"]:
        md_assemblage += ("""

Entre les deux chemins du TROLL, l'export **VuSitu direct est prioritaire** ; la voie
rapatriée par la centrale ne sert qu'à combler ses trous, sans recalage : c'est le même
capteur.""")
    cellules += [md(md_assemblage),
                 code(remplir(ASSEMBLAGE, COLONNES_TROLL=col_troll, DOUBLONS=doublons,
                              PILES=piles, RELAIS=relais, SONDES=sondes_txt,
                              ORDRE=repr(st["ordre"]).replace("'", '"')))]

    cellules += [md(titre("Corrections capteur") + """

Les deux seules corrections qui portent sur une **sonde**, avant toute fusion.

`VOIES_ECARTEES` met des mesures à l'écart : la voie est retirée avant la fusion, donc
une autre sonde prend le relais si elle mesure ; s'il n'y en a pas, la lacune reste et
l'interpolation ne comblera pas plus de 12 h.

`CALAGES_SONDE` déplace une sonde entière, ou son passé, ou son avenir."""),
                 code(remplir(CORRECTIONS, ECARTEES=liste_py(st["voies_ecartees"]),
                              CALAGES=liste_py(st["calages"])))]

    cellules += [md(titre("Comparaison des sources") + """

À lancer pour juger quelle sonde garder sur une période, avant d'écrire une période
imposée dans les cellules suivantes."""),
                 code(remplir(COMPARAISON, GRANDEURS=", ".join('"%s"' % g for g in grandeurs)))]

    cellules += [md(titre("Niveau") + """

La sonde est choisie automatiquement, dans l'ordre `ORDRE` déclaré à l'assemblage.
`SONDE_PRIORITAIRE_NIVEAU` sert à imposer une autre sonde sur une période précise. Les
périodes retenues sont affichées, avec le recalage appliqué à chaque changement."""),
                 code(remplir(NIVEAU, PRIO_NIVEAU=""))]

    cellules += [md(titre("Conductivité")), code(remplir(CONDUCTIVITE, PRIO_COND="")),
                 md("""### Filtre IQR et lissage

Post-traitement appliqué **après** la fusion et le calage sur les points de contrôle :
c'est cette chronique nettoyée qui alimente `full_data` et le fichier final."""),
                 code(remplir(IQR, FENETRE=st["iqr"][0], K=st["iqr"][1],
                              LISSAGE=st["lissage"]))]

    autres = [g for g in grandeurs if g not in ("Niveau_(cm)", "Conductivité")]
    cellules += [md(titre("Température et autres paramètres") + """

Choix automatique, pas de calage sur points de contrôle. Les voies défaillantes ont
déjà été écartées à la cellule des corrections capteur."""),
                 code(remplir(AUTRES, AUTRES=repr(autres).replace("'", '"')))]

    unite = ""
    if st["tarage"]:
        unite = st["tarage"]["unite"]
        cellules += [md(titre("Débit") + "\n\n" + st["tarage"]["note"] +
                        "\nLe débit est calculé après les corrections du niveau, puis recalculé "
                        "sur le\nniveau interpolé."),
                     code(remplir(DEBIT, SEUIL=st["tarage"]["seuil"], UNITE=unite,
                                  CORPS=st["tarage"]["corps"]))]

    md_statuts = titre("Cote NGF, interpolation et statuts") + """

Les lacunes de moins de 12 h sont comblées. `Statut_<grandeur>` dit si la valeur est
mesurée, interpolée ou manquante."""
    if st["ngf"] is not None:
        md_statuts += """

`cote = %s + Niveau_(cm) / 100`. L'ancienne version écrivait `ngf - (ngf - h) / 100`,
qui se simplifie en `%.4f + h / 100` et plaçait donc le zéro %.4f m trop bas.""" % (
            st["ngf"], st["ngf"] - st["ngf"] / 100, st["ngf"] / 100 - 0.0)
    cellules += [md(md_statuts),
                 code(remplir(STATUTS, NGF=repr(st["ngf"]),
                              RECALCUL_Q=remplir(RECALCUL_Q, UNITE=unite).lstrip("\n")
                              if st["tarage"] else ""))]

    n_panneaux = 3 if st["troll"] else 2
    courbe0 = '"Q_(%s)"' % unite if st["tarage"] else '"Niveau_(cm)"'
    label0 = ("Débit (%s)" % unite) if st["tarage"] else "Niveau (cm)"
    cellules += [md(titre("Sauvegarde et graphe de synthèse") + """

Un paramètre par grandeur, avec son statut. Le détail capteur par capteur, et la sonde
retenue à chaque pas, restent dans le fichier consolidé écrit à l'assemblage."""),
                 code(remplir(SAUVEGARDE, UNITE=unite, N_PANNEAUX=n_panneaux,
                              HAUTEUR=10 if n_panneaux == 3 else 7,
                              PANNEAU0=remplir(PANNEAU0, COURBE0=courbe0, LABEL0=label0),
                              PANNEAU2=PANNEAU2 if st["troll"] else "")),
                 md("""### Contrôle des mesures et des interpolations

Un paramètre à la fois, choisi dans le menu du graphe : les pas mesurés en noir, les pas
comblés par interpolation en rouge. Les trous de plus de 12 h restent vides."""),
                 code(INTERPOLATION)]

    return {"cells": cellules, "metadata": gab["metadata"], "nbformat": 4, "nbformat_minor": 5}


if __name__ == "__main__":
    for nom, st in STATIONS.items():
        nb = construire(nom, st)
        chemin = REPO / st["fichier"]
        chemin.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
        lignes = sum(len("".join(c["source"]).splitlines())
                     for c in nb["cells"] if c["cell_type"] == "code")
        print(f"{st['fichier']:60s} {len(nb['cells']):3d} cellules  {lignes:4d} lignes de code")
