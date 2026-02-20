import csv
from pathlib import Path
from datetime import datetime
import sys

# ======================================================
# OUTILS GÉNÉRAUX
# ======================================================

INPUT = Path("input")
OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

def erreur(msg):
    print("\n❌ ERREUR BLOQUANTE :", msg)
    sys.exit(1)


# ======================================================
# LECTURE CSV ROBUSTE (accepte ; ou ,, BOM, casse, espaces)
# ======================================================

def lire_csv_flexible(path: Path):
    """
    Lit un CSV en détectant automatiquement le séparateur , ou ;
    et en gérant le BOM.
    Retourne (rows, headers)
    """
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            except csv.Error:
                dialect = csv.excel
                dialect.delimiter = ","
            reader = csv.DictReader(f, dialect=dialect)
            rows = list(reader)
            headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
            return rows, headers
    except FileNotFoundError:
        erreur(f"Fichier introuvable : {path}")


def normaliser_header(h):
    if h is None:
        return ""
    return h.strip().lower().replace(" ", "").replace("\ufeff", "")


def lire_csv(path: Path):
    """Wrapper simplifié pour les fichiers où on ne valide pas l'en-tête."""
    rows, headers = lire_csv_flexible(path)
    return rows


# ======================================================
# GESTION DES DATES
# ======================================================

def parse_date(s):
    try:
        return datetime.strptime(s, "%d/%m/%Y")
    except:
        erreur(f"Date invalide : '{s}'. Format attendu : dd/mm/yyyy")


# ======================================================
# 1) CHARGER LES JOURS (tri chronologique)
# ======================================================

def charger_jours():
    raw, headers = lire_csv_flexible(INPUT / "jours.csv")
    if not raw:
        erreur("jours.csv est vide !")

    key = None
    for h in headers:
        if normaliser_header(h) == "jour":
            key = h
            break
    if not key:
        erreur(f"jours.csv doit contenir une colonne 'Jour'. En-têtes trouvées: {headers}")

    jours = [row[key].strip() for row in raw]
    dates = [parse_date(j) for j in jours]

    jours_tries = [d.strftime("%d/%m/%Y") for d in sorted(dates)]
    return jours_tries


# ======================================================
# 2) CHARGER MODULES A/B (Module,NbSeances)
# ======================================================

def charger_modules(path: Path):
    rows, headers = lire_csv_flexible(path)
    if not rows:
        erreur(f"{path.name} est vide !")

    # repérage des colonnes
    module_key = None
    nb_key = None

    for h in headers:
        h_norm = normaliser_header(h)
        if h_norm == "module":
            module_key = h
        elif h_norm == "nbseances":
            nb_key = h

    if not module_key or not nb_key:
        erreur(
            f"En-têtes invalides dans {path.name}. "
            f"Trouvées: {headers}. Attendu: Module,NbSeances"
        )

    modules = []
    for i, row in enumerate(rows, start=2):
        nom = (row.get(module_key) or "").strip()
        nb_raw = (row.get(nb_key) or "").strip()

        if not nom:
            erreur(f"{path.name}, ligne {i}: Module vide.")

        try:
            nb = int(nb_raw)
        except:
            erreur(f"{path.name}, ligne {i}: NbSeances doit être un entier. Valeur: {nb_raw}")

        if nb < 1:
            erreur(f"{path.name}, ligne {i}: NbSeances doit être >= 1.")

        modules.append({"module": nom, "nb": nb})

    return modules


# ======================================================
# 3) CHARGER MODULES LIÉS (liens.csv)
# ======================================================

def charger_liens(jours):
    rows, headers = lire_csv_flexible(INPUT / "liens.csv")
    if not rows:
        return {}

    module_key = None
    jour_key = None

    for h in headers:
        h_norm = normaliser_header(h)
        if h_norm == "module":
            module_key = h
        elif h_norm == "jour":
            jour_key = h

    if not module_key or not jour_key:
        erreur("liens.csv doit contenir les colonnes Module,Jour")

    modules_lies = {}

    for i, row in enumerate(rows, start=2):
        m = (row.get(module_key) or "").strip()
        j = (row.get(jour_key) or "").strip()

        if not m or not j:
            erreur(f"liens.csv ligne {i} invalide : {row}")

        if j not in jours:
            erreur(f"Jour imposé '{j}' pour module '{m}' n'existe pas dans jours.csv")

        modules_lies.setdefault(m, []).append(j)

    # tri chronologique des jours imposés
    for m in modules_lies:
        dates = [parse_date(j) for j in modules_lies[m]]
        modules_lies[m] = [d.strftime("%d/%m/%Y") for d in sorted(dates)]

    return modules_lies


# ======================================================
# 4) VALIDATIONS
# ======================================================

def valider_incoherences(modA, modB, liens):
    nomsA = {m["module"] for m in modA}
    nomsB = {m["module"] for m in modB}

    # modules liés ne doivent PAS apparaître dans A/B
    for m in liens:
        if m in nomsA or m in nomsB:
            erreur(
                f"Le module lié '{m}' apparaît dans modules_A.csv "
                "ou modules_B.csv (interdit)."
            )

    # collision de jours imposés
    seen = {}
    for m, jours in liens.items():
        for j in jours:
            if j in seen:
                erreur(
                    f"Collision : le jour {j} est imposé pour {seen[j]} et {m}."
                )
            seen[j] = m


# ======================================================
# 5) CRÉATION PLANNING VIDE
# ======================================================

def planning_vide(jours):
    return {j: "Libre" for j in jours}


# ======================================================
# 6) PLACEMENT MODULES LIÉS
# ======================================================

def placer_modules_lies(planningA, planningB, liens):
    for module, jours in liens.items():
        for j in jours:
            if planningA[j] != "Libre" or planningB[j] != "Libre":
                erreur(
                    f"Jour {j} déjà occupé alors que '{module}' "
                    "doit y être placé."
                )
            planningA[j] = module
            planningB[j] = module


# ======================================================
# 7) PLACEMENT MODULES NON LIÉS (ordre strict, blocs continus)
# ======================================================

def placer_non_lies(planning, modules_non_lies, jours, liens):
    non_places = []

    for mod in modules_non_lies:
        nom = mod["module"]
        nb = mod["nb"]

        count = 0
        for j in jours:
            if count == nb:
                break

            # si jour déjà occupé (module lié ou non lié précédent)
            if planning[j] != "Libre":
                continue

            planning[j] = nom
            count += 1

        if count < nb:
            non_places.append((nom, nb - count))

    return non_places


# ======================================================
# 8) EXPORTS
# ======================================================

def write_csv(path, colonnes, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(colonnes)
        for r in rows:
            w.writerow(r)


def write_excel(planningA, planningB, non_places, jours):
    try:
        import pandas as pd
    except:
        print("ℹ Excel non généré (installe pandas + openpyxl).")
        return

    dfA = pd.DataFrame([(j, planningA[j]) for j in jours],
                       columns=["Jour", "Module"])
    dfB = pd.DataFrame([(j, planningB[j]) for j in jours],
                       columns=["Jour", "Module"])
    dfN = pd.DataFrame(non_places, columns=["Module", "NbNonPlaces"])

    with pd.ExcelWriter(OUTPUT / "planning.xlsx", engine="openpyxl") as writer:
        dfA.to_excel(writer, sheet_name="Planning A", index=False)
        dfB.to_excel(writer, sheet_name="Planning B", index=False)
        dfN.to_excel(writer, sheet_name="Non Places", index=False)


# ======================================================
# 9) MAIN
# ======================================================

def main():
    print("⏳ Chargement...")

    jours = charger_jours()
    modA = charger_modules(INPUT / "modules_A.csv")
    modB = charger_modules(INPUT / "modules_B.csv")
    liens = charger_liens(jours)

    valider_incoherences(modA, modB, liens)

    planningA = planning_vide(jours)
    planningB = planning_vide(jours)

    placer_modules_lies(planningA, planningB, liens)

    noms_lies = set(liens.keys())
    non_lies_A = [m for m in modA if m["module"] not in noms_lies]
    non_lies_B = [m for m in modB if m["module"] not in noms_lies]

    non_places = []
    non_places += placer_non_lies(planningA, non_lies_A, jours, liens)
    non_places += placer_non_lies(planningB, non_lies_B, jours, liens)

    write_csv(OUTPUT / "planning_A.csv", ["Jour", "Module"],
              [(j, planningA[j]) for j in jours])

    write_csv(OUTPUT / "planning_B.csv", ["Jour", "Module"],
              [(j, planningB[j]) for j in jours])

    write_csv(OUTPUT / "modules_non_places.csv",
              ["Module", "NbNonPlaces"], non_places)

    write_excel(planningA, planningB, non_places, jours)

    print("✔ Planning généré dans output/")
    print("✔ Terminé avec succès !")

if __name__ == "__main__":
    main()
