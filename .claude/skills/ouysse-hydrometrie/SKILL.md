---
name: ouysse-hydrometrie
description: Post-traitement des chroniques des stations hydrometriques du systeme karstique de l'Ouysse (Causses du Quercy). A utiliser des que la conversation porte sur les notebooks de consolidation Fontbelle ou Cabouy, les sondes CTD Diver / Aqua TROLL / centrale OTT, la compensation barometrique, le raccordement de chroniques, les points de controle (punctual_measurements), le recalage d'echelle limnimetrique, le filtre IQR sur la conductivite, la courbe de tarage, la cote NGF, ou tout fichier Cabouy_*.ipynb / Fontbelle_*.ipynb.
---

# Consolidation des stations hydrometriques de l'Ouysse

Proprietaire : Gaetan Tollet, hydrogeologue. Un notebook par station, tenu a la main,
qui sert aussi d'historique des corrections appliquees. Le notebook EST l'outil : pas de
package, pas de classe, pas d'abstraction ajoutee.

## 1. Modele instrumental

Trois appareils, quatre jeux de mesures. Ne pas confondre.

| Appareil | Niveau | Cond. | Temp. | Autres | Acquisition |
|---|---|---|---|---|---|
| **CTD** (Diver autonome) | oui, compense baro | oui | oui | - | releves par campagnes |
| **TROLL** (Aqua TROLL / VuSitu) | **non** | oui | oui | turbidite, chlorophylle, O2 | exports directs |
| **Centrale OTT** | oui, **sa propre sonde CTD** | oui (sa CTD) | oui (sa CTD) | reprend le TROLL | enregistrement continu |

Consequences :

- **2 niveaux** : la CTD autonome et la CTD de la centrale. Ce sont **deux capteurs
  distincts**, pas un doublon.
- **3 conductivites et 3 temperatures propres** : CTD, TROLL, CTD de la centrale.
  **4 en comptant** la voie TROLL rapatriee par la centrale, qui est un **vrai doublon**
  du TROLL direct.
- Les voies `C1`/`T1`/`level` de la centrale viennent de SA CTD. Les voies
  `C2`/`T2`/`Turbi`/`O2`/`Chlorophyl` viennent du TROLL et doublonnent les exports directs.

## 2. Nomenclature des colonnes

| Colonne | Origine |
|---|---|
| `Niveau_CTD_(cm)` | CTD autonome (+ ancien fichier consolide, meme grandeur) |
| `Niveau_CTDOTT_(cm)` | sonde CTD de la centrale (champ `level`) |
| `Cond_CTD_(µS/cm)`, `Temp _CTD(°C)` | CTD autonome (noter l'espace avant `_CTD` sur la temperature) |
| `Cond_Troll_(µS/cm)`, `température_Troll_(°C)` | TROLL direct |
| `Cond_CTDOTT_(µS/cm)`, `Temp_CTDOTT_(°C)` | CTD de la centrale (`C1`, `T1`) |
| `Cond_TrollOTT_(µS/cm)`, `Temp_TrollOTT_(°C)` | TROLL via la centrale (`C2`, `T2`) : doublon |
| `Turbidity_*`, `O2_*`, `FluorescenceChloro_a_*` | TROLL direct et via centrale |
| `<voie directe> + centrale` | les deux chemins d'UNE sonde reunis sans recalage (TROLL) |
| `Niveau_(cm)`, `Conductivité`, `Température`, ... | grandeurs de **synthese**, une par parametre |
| `<parametre>_source` | voie retenue, pas par pas |
| `Statut_<parametre>` | Mesuree / Interpolee / Manquante |

## 3. Ordre de priorite

Defaut : **OTT > TROLL > CTD**, declare une fois dans `ORDRE` (cellule 8). Le choix
est **automatique** : a chaque pas, la premiere sonde de l'ordre qui mesure. On sort
de ce choix par une liste d'**exceptions** `(debut, fin, sonde imposee)`, une par
grandeur, ecrite au-dessus de son graphe de correction. `choisir_sondes` refuse une
entree mal formee (pas trois champs, sonde inconnue, fin anterieure au debut) en
nommant la ligne fautive, et dit pour chaque exception combien de pas changent
reellement de sonde : une exception sans effet, parce que la sonde etait deja celle
du choix automatique ou qu'elle ne mesure pas sur la periode, se voit tout de suite. Le niveau n'existe que sur
OTT et CTD.

On ne change pas de sonde pour boucher un trou de moins de 12 h : c'est
l'interpolation qui s'en charge. Un basculement plus court est absorbe par la
periode precedente. Une panne plus longue fait bien passer la main a la sonde
suivante.

Le recalage est **chaine** : a chaque changement de periode, la sonde qui devient
prioritaire est recalee sur la precedente, mediane des ecarts sur les **24 pas communs
les plus proches de la transition**, de part et d'autre. C'est le calcul que
l'utilisateur fait a la main, et il rend la chronique continue a la jonction. Une
fenetre large (30 jours, essayee puis abandonnee) melange la derive de fin de vie de
la sonde qui s'arrete avec son comportement normal, et laisse une marche de plusieurs
centaines d'unites a la jonction. La premiere periode fixe le zero. Sans recouvrement,
raccord bout a bout si le trou fait moins de 12 h ; au-dela, aucun recalage et le trou
reste.

Chaque periode n'utilise **que** sa sonde : aucune autre ne vient combler ses
lacunes. Les deux chemins d'acquisition d'une MEME sonde (TROLL direct et TROLL
rapatrie par la centrale) sont reunis **avant**, sans recalage : un decalage entre eux
n'aurait pas de sens physique, c'est une difference de resolution d'enregistrement.

Un decalage doit pouvoir etre **fige en dur** (`CALAGES_SONDE`) ; un decalage
recalcule a chaque execution n'est pas reproductible.

## 4. Les deux stations

| | Fontbelle | Cabouy |
|---|---|---|
| `PREFIXE_CTD` | `Fontbelle` | `Cabouy` |
| Colonne fuseau CTD | `UTC fichier` (minuscule) | `UTC Fichier` |
| Colonne fuseau TROLL | `UTC Fichier` | `UTC Fichier` |
| Sortie hauteur | **debit** (courbe de tarage ; la **2e** courbe est la bonne) | **cote NGF**, zero a 107.6158 |
| IQR conductivite | `48h`, k=0.8, toute la chronique | `800h`, k=1.5, toute la chronique |
| Periodes ecartees autres | - | `Temp _CTD(°C)` 2023, `O2_(mg/l)` 2021 |
| Baro | `Patm Ouysse Calès [hPa]` | idem |

Faits de terrain Cabouy :

- Echelle limnimetrique **deplacee en juin 2024**. Deplacer l'echelle ne deplace pas le
  capteur : la mesure reste continue, il n'y a pas de marche a corriger a cette date.
  Seules les **lectures** changent de reference.
- Le `+56.5 cm` de la V2 etait un recalage visuel entre deux chroniques, sans mesure
  derriere. Ne pas le reintroduire comme une constante physique.
- Lectures sures : **03/04/2026 10:00 UTC = 109 cm** (carnet, nouvelle echelle) et
  **06/12/2024 16:00 = 107 cm** sur la centrale.
- `DECALAGE_CTD = 76.86` cm, valide par l'utilisateur, fige. Dans la V5 il vit dans
  `DECALAGES_FIGES[("Niveau_(cm)", "CTD")]`.
- L'ecart entre les zeros des deux echelles n'a **jamais ete mesure**. Tant que
  `DECALAGE_ECHELLES` vaut `None`, les lectures faites sur l'ancienne echelle sont
  tracees mais jamais utilisees pour corriger, et le journal dit pourquoi.
- Cote NGF : tranche. La formule de la V2, `ngf - (ngf - h) / 100`, se simplifie en
  `106.5396 + h / 100` et placait donc le zero 1.076 m trop bas. La V6 ecrit
  `107.6158 + h / 100`. Les cotes NGF sont superieures de 1.0762 m a celles de la V2.
- Le filtre IQR de la conductivite s'applique desormais a **toute** la chronique :
  la borne au 2021-02-14 a ete retiree a la demande de l'utilisateur.

## 5. Structure du notebook (15 sections, ordre impose)

1 Imports | 2 Chemins | 3 Fonctions (lecture, puis correction : 2 cellules) | 4 CTD
(UTC + baro) | 5 Raccordement a l'ancienne chronique | 6 TROLL | 7 Centrale OTT
| 8 Assemblage : une colonne par sonde, doublons TROLL reunis, `ORDRE`
| 9 Corrections capteur : `VOIES_ECARTEES` + `CALAGES_SONDE` | 10 Comparaison des
sources (un graphe, rien d'autre) | 11 Niveau | 12 Conductivite | 13 Temperature et
autres | 14 Cote NGF + interpolation + statuts | 15 Sauvegarde + graphe de synthese

Chaque cellule de correction porte ses reglages **juste au-dessus de son graphe** :
`SONDE_PRIORITAIRE_NIVEAU`, `SONDE_PRIORITAIRE_COND`, `EXCEPTIONS` pour les autres
grandeurs (sonde imposee sur une periode). Le generateur de periodes a copier-coller
a existe puis a ete supprime : le choix etant redevenu automatique, il ne servait plus.
La conductivite est coupee en deux cellules : fusion + calage sur les points de
controle, puis **filtre IQR et lissage dans une cellule separee**, dont la sortie est
celle qui alimente `full_data` et le fichier final.

Tout reglage se declare **en tete de la cellule qui l'utilise**, jamais en cellule 2.
L'utilisateur corrige au jugement, en aller-retour avec le graphe de la meme cellule.

### Minimalisme

Contrainte forte, rappelee par l'utilisateur apres une V5 trop verbeuse : le notebook
doit rester **plus court que la V2** (907 lignes de code). La V6 en fait 584. Sont
explicitement rejetes : les fonctions qui ne servent qu'une fois, les journaux en
DataFrame affiches par `display`, les tableaux recapitulatifs quand un graphe dit la
meme chose (ecarts entre sondes, couverture), les graphes de diagnostic en plus du
graphe de correction, les reglages non demandes (un seuil `NIVEAU_MINI`, par exemple).
Un `print` d'une ligne remplace un tableau. Quand deux formules ou deux methodes
coexistent "au choix", en trancher une et annoncer l'effet chiffre.

En revanche les **graphes de decision** sont demandes : chaque cellule de correction
trace les sondes qui entrent dans la fusion, la fusion avant correction et la
chronique finale, sur un seul graphe. La legende doit dire de combien chaque sonde a
ete recalee et par rapport a laquelle, sinon le trace est inexploitable.

## 6. Pieges de format, deja traites, ne pas regresser

| Source | Piege | Traitement en place |
|---|---|---|
| Diver CSV | en-tete a une ligne variable, pied `END OF DATA`, encodages multiples, virgule decimale, conductivite en mS ou µS | en-tete et pied reperes **par contenu** ; unite lue dans les crochets du libelle |
| VuSitu CSV | guillemets parasites, numero de serie dans le nom de colonne | guillemets retires, serie retiree par regex |
| OTT CSV | `-99999` = absence, horodatages en double, voies qui demarrent a des dates differentes | sentinelles mises a NaN, mediane par horodatage |
| Tables UTC | nom de fichier absent ou mal saisi (extension oubliee, espace) | correspondance **exacte**, avertissement nommant le fichier, campagne ignoree. Pas de rattrapage automatique : c'est la table de metadonnees qui se corrige |
| Campagnes CTD | recouvrements, donc horodatages en double | `drop_duplicates(subset="DATE")` au passage sur la grille horaire, comme la V2 : la premiere valeur gagne. **Pas de mediane** |

## 7. Physique et unites

- `1 hPa = 1.019716 cmH2O`. La V2 soustrayait des hPa a des cmH2O, ce qui injectait 2 %
  des variations barometriques dans le niveau. La constante `HPA_EN_CMH2O` permet de
  revenir a l'ancienne formule avec `1.0` pour comparer.
- Le niveau compense n'a **pas d'origine absolue** tant qu'il n'est pas cale. Donc
  **aucun seuil sur le niveau dans `GAMMES`** : les bornes physiques ne concernent que
  conductivite, temperature, turbidite, O2, chlorophylle. Un seuil metier (sonde emergee)
  se pose apres calage, sur la serie calee.
- Les points de controle s'appliquent par defaut **vers l'aval** et en cascade : un point
  mal date decale tout ce qui suit.
- Le **sens** d'une correction de niveau se choisit, il ne se devine pas :
  `aval` pour une marche reelle (capteur deplace, redescendu), `amont` pour ramener un
  segment historique sur la reference actuelle sans toucher au present, `tout` pour un
  calage global. Une **echelle** deplacee n'est aucun des trois : le capteur n'a pas
  bouge, la serie n'a pas de marche, ce sont les **lectures** qui changent de reference.
- La cote NGF se recalcule depuis le niveau interpole, elle ne s'interpole pas.

## 8. Regles de travail

Ces regles visent des erreurs deja commises sur ce projet.

1. **Suivre le code de l'utilisateur de pres.** Corriger, pas reecrire. Toute abstraction
   ajoutee a ete rejetee : package, dictionnaire de priorites a rallonge, mecanique de
   recalage a quatre etages.
2. **Ne jamais retirer une correction existante sans le dire.** Si une constante parait
   redondante, le demander ; elle encode souvent un fait de terrain.
3. **Idempotence.** Une cellule de correction lit `BRUT` et ecrit `full_data`. Jamais
   lire et ecrire la meme colonne : relancer cumulerait les decalages et interdirait
   l'essai/erreur.
4. **Mettre a NaN, ne pas supprimer de lignes.** Sur une grille horaire reguliere, une
   lacune doit se voir. La V2 supprimait les lignes et Plotly reliait les points, ce qui
   masquait la perte.
5. **Tout journaliser.** Chaque point de controle apparait dans le journal, applique ou
   non, avec le motif du refus. Un tableau vide sans explication n'est pas un resultat.
6. **`go.Scattergl`, jamais `go.Scatter`.** Une chronique horaire pluriannuelle fait
   planter le navigateur en rendu SVG.
7. **`fig.show()` sans `return fig`.** Sinon Jupyter affiche la figure deux fois.
8. **Executer avant de livrer.** Tout changement se verifie sur un jeu de test synthetique
   couvrant la periode concernee, pas seulement en relisant le diff.
9. **Annoncer tout changement de comportement numerique**, meme correct, avec l'ordre de
   grandeur de l'effet sur les chiffres de l'utilisateur.
10. **Pas de rattrapage approximatif.** Une correspondance tolerante sur un nom de fichier
    ou une date masque une erreur de saisie au lieu de la faire corriger. Avertir en
    nommant precisement ce qui cloche, et s'arreter la.
11. Reponses en francais, sans preambule ni conclusion de politesse. Pas de suggestion non
    demandee. Pas de tiret cadratin ni de guillemet typographique dans le code.

## 9. Etat

`Code pour consolider les donnees-Cabouy_V4.ipynb` (depot `tolletg/station`, branche
`main`) est la version de reference : c'est le notebook que l'utilisateur fait tourner,
avec SA chronique corrigee (periodes imposees, voies ecartees, calages). Il descend de
`Cabouy_consolidation_V6.ipynb`, garde ici comme historique. 674 lignes de code,
37 cellules, contre 907 pour la V2. Ne jamais ecraser ses listes de corrections.

- Trois sondes : CTD, TROLL, OTT. Entre les deux chemins du TROLL, l'export VuSitu
  **direct est prioritaire** et la voie rapatriee par la centrale ne comble que ses
  trous, sans recalage.
- `SONDES` = {grandeur: {sonde: colonne}} et `ORDRE`, declares une fois en cellule 8.
- `VOIES_ECARTEES` et `CALAGES_SONDE` vivent ensemble en **cellule 9**, separes de
  l'assemblage : un aller-retour avec les graphes ne demande de relancer que cette
  cellule. `BRUT` (cellule 8) reste l'instantane brut, `CORRIGE` porte les mises a
  l'ecart, `voies_calees(grandeur)` y ajoute les calages.
- `VOIES_ECARTEES` = [(debut, fin, colonne, motif)] : le SEUL mecanisme de
  mise a l'ecart, toutes grandeurs confondues. Il agit sur la voie brute, avant la
  fusion, donc une autre sonde prend le relais si elle mesure. Les listes
  `PERIODES_ECARTEES_<GRANDEUR>`, qui faisaient doublon avec un autre format de tuple,
  ont ete supprimees : c'etait la source d'erreurs "too many values to unpack".
  `ecarter` refuse une entree qui n'a pas quatre champs, en la nommant.
- `CALAGES_SONDE` = [(date, sonde, grandeur, decalage, sens)] : les
  ajustements manuels, hors points de controle. `voies_calees(grandeur)` les applique
  et les affiche. Entree validee : `("2024-12-06 16:00", "CTD", "Niveau_(cm)", 76.86,
  "amont")`. Attention, plusieurs entrees en sens `"tout"` se cumulent sur toute la
  serie, ce n'est pas toujours ce que l'utilisateur attend.
- `choisir_sondes(voies, ORDRE, exceptions)` decoupe en periodes, `fusionner` les
  enchaine et recale. Les deux affichent ce qu'ils font, periode par periode.
- `decaler(serie, date, valeur, sens)` avec `amont` / `aval` / `tout`.
- Cellule 5 : le raccord a l'ancienne chronique est toujours mesure a la jonction.
  `RACCORD_FIGE`, qui permettait de le figer, a ete supprime : il ne servait pas.
  Graphe niveau ET conductivite autour du raccord.
- Les points de controle de `punctual_measurements.xlsx` suffisent pour l'aval ;
  chaque point applique ou refuse sort en une ligne de `print`.
- Cellule 9 : un seul graphe, les sondes brutes superposees, pour juger laquelle
  garder. Les cellules 10 et 11 tracent en plus la fusion et la chronique finale.
- Cellule 15 : `Cabouy_final.xlsx` porte la valeur et le statut de chaque grandeur,
  **sans les colonnes `_source`** (le detail sonde par sonde reste dans le fichier
  consolide de la cellule 8). Le graphe de synthese a trois panneaux : niveau et
  pluie, conductivite et temperature, turbidite + oxygene + chlorophylle (troisieme
  axe decale vers l'exterieur, comme dans la V2). Suit un graphe de controle des
  interpolations, un menu deroulant par grandeur, mesure en noir et interpole en
  rouge, qui remplace l'application Dash de la V2.

`tests/jeu_de_test_cabouy.py` fabrique un jeu synthetique 2019-2026 avec tous les
pieges de format, execute toutes les cellules de code et verifie 46 proprietes : le trou laisse par une voie
ecartee, le refus d'une entree mal formee, l'exclusivite des periodes, l'ordre automatique, une
exception qui impose sa sonde, un basculement de 5 h absorbe, une panne de 50 h qui
passe la main, la continuite a une transition avec recouvrement, le raccord bout a
bout sur un trou de 6 h, l'absence de recalage sur un trou de 60 h, l'idempotence de
la cellule du niveau, les trois sens de `decaler`, la formule NGF, et le fait que le
notebook reste plus court que la V2 :

    python3 tests/jeu_de_test_cabouy.py "Code pour consolider les donnees-Cabouy_V4.ipynb" <dossier>

Les tests lisent les reglages DANS le notebook (`VOIES_ECARTEES`, `CALAGES_SONDE`,
`SONDE_PRIORITAIRE_COND`) au lieu de figer les valeurs de l'utilisateur : quand il
change une periode, le test suit.

Fontbelle n'a pas encore ete porte sur ce modele.
