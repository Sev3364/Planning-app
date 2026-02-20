Générateur de Planning A+B (Modules liés + Modules non liés)
Ce projet est un moteur de génération de planning permettant de produire deux plannings synchronisés (Planning A et Planning B) à partir de fichiers CSV d’entrée.
Il gère :

✔ Des modules liés, placés obligatoirement à des jours imposés, et synchronisés entre A et B
✔ Des modules non liés, respectant strictement l’ordre des fichiers modules_A.csv et modules_B.csv
✔ Des blocs continus pour les modules non liés
✔ Les jours non utilisés remplis automatiquement avec “Libre”
✔ Un tri automatique des jours (jours.csv)
✔ Un export CSV + un export Excel multi‑onglets (planning.xlsx)
✔ De nombreuses validations strictes avec erreurs bloquantes pour garantir la cohérence


📁 Structure du projet
planning-app/
│
├── main.py
│
├── input/
│   ├── jours.csv
│   ├── modules_A.csv
│   ├── modules_B.csv
│   └── liens.csv
│
└── output/
    ├── planning_A.csv
    ├── planning_B.csv
    ├── modules_non_places.csv
    └── planning.xlsx


🧠 Règles principales du moteur
🔵 Jours (jours.csv)

Format dd/mm/yyyy
Peuvent être dans n'importe quel ordre → le moteur les trie automatiquement
Un seul module par jour (A et B)


🔵 Modules liés (liens.csv)

Les modules liés sont définis uniquement dans liens.csv
1 ligne = 1 séance imposée
Le module doit apparaître dans les deux plannings au même jour
Les jours sont normalisés automatiquement
Format attendu :

Module,Jour
Math,03/03/2026
Math,07/03/2026
Histoire,10/03/2026

Règles strictes :

Jour doit exister dans jours.csv
Jours triés automatiquement
Pas de doublon de jour
Pas de collision entre deux modules liés
Si un module lié apparaît dans modules_A ou modules_B → erreur bloquante


🔵 Modules non liés (modules_A.csv / modules_B.csv)

Format :

Module,NbSeances


L’ordre des lignes détermine l’ordre absolu du placement
Placement en blocs continus
Si un jour imposé passe au milieu d’un bloc → on reprend le bloc ensuite
Si un module ne rentre pas → il est listé dans modules_non_places.csv


🔵 Sorties
Dans output/ :

planning_A.csv
planning_B.csv
modules_non_places.csv
planning.xlsx (3 onglets : A, B, non placés)


▶️ Exécuter le programme
Dans un terminal (VS Code ou PowerShell), à la racine du projet :
Shellpython main.pyAfficher plus de lignes
Le programme génère automatiquement les fichiers dans output/.

📦 Export Excel (optionnel)
Si vous souhaitez générer planning.xlsx, installez :
Shellpip install pandas openpyxlAfficher plus de lignes

❗ Erreurs bloquantes possibles
Le programme s’arrête immédiatement si :

un jour imposé n’existe pas dans jours.csv
un module lié apparaît dans modules_A ou modules_B
un module lié n’a pas de jour imposé
deux modules liés exigent le même jour
un module non lié a un nb de séances invalide
un format de date est incorrect

Les messages d’erreur sont explicites et indiquent la ligne fautive.

🎯 Objectif du projet
Ce moteur a été conçu pour gérer :

des plannings pédagogiques complexes
des contraintes strictes
deux classes / deux groupes en parallèle
des modules synchronisés
des modules non liés dans un ordre imposé

Il permet de générer rapidement un planning fiable, cohérent, reproductible et facile à adapter.

🤝 Contact / Collaboration
Ce projet est versionné sur GitHub pour permettre :

la sauvegarde
la collaboration
l’évolution du code
la reproductibilité
l’historique complet

N’hésitez pas à créer une issue si vous souhaitez suggérer une amélioration.
