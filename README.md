# Calculateur import véhicule (Chine → Algérie)

Petite application Flask pour s'entraîner au développement web en partant de zéro.
Aucun compte, aucun paiement, aucun service cloud : tout tourne sur ton ordinateur.

## Ce qu'elle fait

Tu remplis un formulaire (prix FOB, transport, douane, taux de change) et
l'appli calcule le coût total estimé de l'importation, en USD et en DZD.

---

## Protocole — préparation du terrain

### 1. Vérifier que Python est installé

Ouvre un terminal et tape :

```bash
python3 --version
```

Si une version s'affiche (ex: `Python 3.11.x`), c'est bon. Sinon, installe
Python depuis [python.org](https://www.python.org/downloads/) (coche bien
"Add Python to PATH" pendant l'installation si tu es sous Windows).

### 2. Un éditeur de code (si tu n'en as pas déjà un)

[VS Code](https://code.visualstudio.com/) est gratuit et le plus utilisé.
Pas obligatoire pour faire tourner l'appli, mais utile pour lire/modifier le code.

### 3. Placer les fichiers

Dézippe le dossier `import-calculator` où tu veux sur ton ordinateur, puis
ouvre un terminal **dans ce dossier** (`cd chemin/vers/import-calculator`).

### 4. Créer un environnement virtuel

Un environnement virtuel isole les librairies Python de ce projet du reste
de ton système — évite que les projets se marchent dessus.

```bash
python3 -m venv venv
```

Puis active-le :

- **Mac/Linux** : `source venv/bin/activate`
- **Windows** : `venv\Scripts\activate`

Tu dois voir `(venv)` apparaître au début de ta ligne de terminal.

### 5. Installer Flask

```bash
pip install -r requirements.txt
```

### 6. Lancer l'application

```bash
python3 app.py
```

Tu devrais voir dans le terminal quelque chose comme :
`Running on http://127.0.0.1:5000`

### 7. Ouvrir dans le navigateur

Va sur **http://127.0.0.1:5000** dans ton navigateur (Chrome, Safari...).
Le formulaire doit s'afficher.

---

## Accéder depuis ton smartphone (sans cloud)

Ton ordinateur et ton téléphone doivent être connectés **au même wifi**.

1. Trouve l'adresse IP locale de ton ordinateur :
   - **Mac** : `ifconfig | grep "inet "` (cherche une adresse type `192.168.x.x`)
   - **Windows** : `ipconfig` (cherche "Adresse IPv4")
   - **Linux** : `hostname -I`
2. L'appli tourne déjà avec `host='0.0.0.0'` dans `app.py` — donc c'est déjà prêt.
3. Sur ton téléphone, ouvre le navigateur et va sur `http://<IP_DE_TON_PC>:5000`
   (ex: `http://192.168.1.42:5000`).

Si ça ne marche pas, vérifie que le pare-feu de ton PC n'est pas en train de
bloquer le port 5000.

---

## Pour aller plus loin (une fois à l'aise)

- Ajouter une vraie base de données (SQLite) pour sauvegarder l'historique
  des calculs.
- Ajouter un taux de change automatique via une API gratuite (au lieu de le
  taper à la main).
- Mettre l'appli en ligne gratuitement (sans carte bancaire) avec
  [PythonAnywhere](https://www.pythonanywhere.com/) (offre gratuite) —
  utile seulement si tu veux y accéder sans être sur ton wifi perso.

## Structure du projet

```
import-calculator/
├── app.py              → la logique Python (routes + calcul)
├── requirements.txt    → la liste des librairies à installer (juste Flask)
├── templates/
│   └── index.html      → le formulaire + l'affichage du résultat
└── README.md           → ce fichier
```
