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

Defaut : **OTT > TROLL > CTD**. Doit rester modifiable, et surchargeable **par periode**
avant toute correction. Le niveau n'existe que sur OTT et CTD.

Regle de recalage : la voie de secours est ramenee sur la voie retenue (decalage median
sur le recouvrement), jamais l'inverse. Un decalage doit pouvoir etre **fige en dur** ;
un decalage recalcule a chaque execution n'est pas reproductible.

Toutes les sondes sont ramenees sur **une seule reference**, la premiere de l'ordre par
defaut. La surcharge par periode ne change alors que le choix de la sonde, pas le zero :
aucune marche aux bornes de la periode. Les deux chemins d'acquisition d'une MEME sonde
(TROLL direct et TROLL rapatrie par la centrale) sont reunis **avant**, sans recalage :
un decalage entre eux n'aurait pas de sens physique, mais il se mesure et s'affiche, car
un ecart non nul voudrait dire que l'hypothese du doublon est fausse.

## 4. Les deux stations

| | Fontbelle | Cabouy |
|---|---|---|
| `PREFIXE_CTD` | `Fontbelle` | `Cabouy` |
| Colonne fuseau CTD | `UTC fichier` (minuscule) | `UTC Fichier` |
| Colonne fuseau TROLL | `UTC Fichier` | `UTC Fichier` |
| Sortie hauteur | **debit** (courbe de tarage ; la **2e** courbe est la bonne) | **cote NGF**, zero a 107.6158 |
| IQR conductivite | `48h`, k=0.8, toute la chronique | `800h`, k=1.5, jusqu'au 2021-02-14 |
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
- Cote NGF : la formule de la V2 place le zero a **106.5396**, pas a 107.6158 comme
  annonce. Ecart de 1.076 m, non tranche. `FORMULE_NGF` expose les deux.

## 5. Structure du notebook (14 sections, ordre impose)

1 Imports | 2 Chemins | 3 Fonctions (lecture, puis correction : 2 cellules) | 4 CTD
(UTC + baro) | 5 Raccordement a l'ancienne chronique | 6 TROLL | 7 Centrale OTT
| 8 Assemblage : une colonne par sonde, doublons TROLL reunis, voies ecartees
| 9 Proposition de periodes (a lancer une fois, sortie a copier-coller)
| 10 Niveau | 11 Conductivite | 12 Temperature et autres | 13 Cote NGF +
interpolation + statuts | 14 Sauvegarde + graphe de synthese

Chaque cellule de correction porte ses propres reglages **juste au-dessus de son
graphe** : `PERIODES_*` (quelle sonde prioritaire quand), `DECALAGES_*`,
`PERIODES_ECARTEES_*`. Tout est **ecrit en dur** : rien n'est recalcule a la volee,
changer une periode ne deplace donc pas les corrections deja calees. La cellule 9
propose ces listes une fois, a partir de la disponibilite reelle des sondes.

Tout reglage se declare **en tete de la cellule qui l'utilise**, jamais en cellule 2.
L'utilisateur corrige au jugement, en aller-retour avec le graphe de la meme cellule.

### Minimalisme

Contrainte forte, rappelee par l'utilisateur apres une V5 trop verbeuse : le notebook
doit rester **plus court que la V2** (907 lignes de code). La V6 en fait 584. Sont
explicitement rejetes : les fonctions qui ne servent qu'une fois, les journaux en
DataFrame affiches par `display`, les tableaux recapitulatifs quand un graphe dit la
meme chose (ecarts entre sondes, couverture), les graphes de diagnostic en plus du
graphe de correction, les reglages non demandes (un seuil `NIVEAU_MINI`, par exemple).
Un `print` d'une ligne remplace un tableau.

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

`Cabouy_consolidation_V6.ipynb` (depot `tolletg/station`) est la version de reference.
584 lignes de code, 15 cellules. Elle repart de la V2 et y ajoute la centrale OTT.

- Trois sondes : CTD, TROLL, OTT. Le TROLL rapatrie par la centrale est reuni au
  TROLL direct **sans recalage** ; l'ecart median entre les deux chemins est affiche.
- `SONDES` = {grandeur: {sonde: colonne}}, declare une fois en cellule 8.
- `PERIODES_<GRANDEUR>` = [(debut, fin, sonde prioritaire)], en dur, au-dessus du
  graphe de correction. `fusionner` prend la sonde prioritaire et laisse les autres
  combler ses trous, dans l'ordre du dictionnaire.
- `DECALAGES_<GRANDEUR>` en dur ramene chaque sonde sur la derniere en service.
- `CALAGE_CTD = ("2024-12-06 16:00", 76.86, "amont")` : la valeur en dur du calage du
  niveau CTD. L'utilisateur a mentionne 75.67 dans un echange, 76.86 est la valeur
  validee ; a retrancher si besoin.
- `decaler(serie, date, valeur, sens)` avec sens `amont` / `aval` / `tout` : la seule
  trace du raisonnement echelle-contre-capteur, tout le reste a ete supprime.
- Les points de controle de `punctual_measurements.xlsx` suffisent pour l'aval ;
  chaque point applique ou refuse sort en une ligne de `print`.

`tests/jeu_de_test_cabouy.py` fabrique un jeu synthetique 2019-2026 avec tous les
pieges de format, execute les 15 cellules et verifie 17 proprietes, dont le trou
laisse par `PERIODES_ECARTEES_NIVEAU`, l'idempotence de la cellule du niveau, les
trois sens de `decaler` et le fait que le notebook reste plus court que la V2 :

    python3 tests/jeu_de_test_cabouy.py Cabouy_consolidation_V6.ipynb <dossier>

Fontbelle n'a pas encore ete porte sur ce modele.
