"""
Calculateur de coût d'importation véhicule (Chine -> Algérie)
--------------------------------------------------------------
Petite application Flask pour s'entraîner :
- une route ("/") qui affiche un formulaire (GET) et traite son envoi (POST)
- un calcul simple en Python pur (pas besoin de base de données pour ce V1)
- un template Jinja (index.html) qui affiche le formulaire + le résultat
"""

from datetime import date, timedelta

import requests
from flask import Flask, redirect, render_template, request, url_for

import db

# On crée l'objet application. __name__ dit à Flask où se trouve ce fichier,
# pour qu'il sache où chercher le dossier "templates".
app = Flask(__name__)
db.init_db()

FRANKFURTER_URL = "https://api.frankfurter.dev/v1"


def calc_tendance(valeurs):
    """Compare les deux dernières valeurs d'une série pour dire si ça monte ou descend."""
    if len(valeurs) < 2:
        return None
    precedent, dernier = valeurs[-2], valeurs[-1]
    diff = dernier - precedent
    if diff == 0:
        return {'sens': 'stable', 'diff': 0, 'pct': 0}
    return {
        'sens': 'hausse' if diff > 0 else 'baisse',
        'diff': abs(diff),
        'pct': abs(diff / precedent * 100) if precedent else None,
    }


def get_eur_usd():
    """Récupère le taux EUR/USD actuel + historique 90 jours (API gratuite, sans clé)."""
    resultat = {'actuel': None, 'historique': []}

    try:
        r = requests.get(
            f"{FRANKFURTER_URL}/latest",
            params={'base': 'EUR', 'symbols': 'USD'},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        resultat['actuel'] = {'taux': data['rates']['USD'], 'date': data['date']}
    except (requests.RequestException, KeyError, ValueError):
        pass

    try:
        fin = date.today()
        debut = fin - timedelta(days=90)
        r = requests.get(
            f"{FRANKFURTER_URL}/{debut.isoformat()}..{fin.isoformat()}",
            params={'base': 'EUR', 'symbols': 'USD'},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        resultat['historique'] = [
            {'date': jour, 'taux': valeurs['USD']}
            for jour, valeurs in sorted(data['rates'].items())
        ]
    except (requests.RequestException, KeyError, ValueError):
        pass

    resultat['tendance'] = calc_tendance([p['taux'] for p in resultat['historique']])
    return resultat


@app.route('/', methods=['GET', 'POST'])
def index():
    resultat = None
    erreur = None

    if request.method == 'POST':
        # request.form contient les valeurs envoyées par le formulaire HTML.
        # On les récupère et on les convertit en nombres (float).
        try:
            prix_fob = float(request.form['prix_fob'])
            transport = float(request.form['transport'])
            assurance = float(request.form.get('assurance') or 0)
            taux_douane = float(request.form['taux_douane'])
            taux_change = float(request.form['taux_change'])

            # --- Le calcul métier ---
            # Valeur CIF = Cost + Insurance + Freight (base classique en douane)
            valeur_cif = prix_fob + transport + assurance

            # Droits de douane calculés sur la valeur CIF
            droits_douane = valeur_cif * taux_douane / 100

            total_usd = valeur_cif + droits_douane
            total_dzd = total_usd * taux_change

            resultat = {
                'valeur_cif': round(valeur_cif, 2),
                'droits_douane': round(droits_douane, 2),
                'total_usd': round(total_usd, 2),
                'total_dzd': round(total_dzd, 2),
            }
        except (ValueError, KeyError):
            erreur = "Merci de remplir les champs obligatoires avec des nombres valides."

    # render_template va chercher templates/index.html et lui transmet
    # les variables "resultat" et "erreur" pour qu'il les affiche.
    return render_template('index.html', resultat=resultat, erreur=erreur, active='calc')


@app.route('/guide')
def guide():
    return render_template('guide.html', active='guide')


@app.route('/marche')
def marche():
    eur_usd = get_eur_usd()
    fret = db.lister_fret()
    tendance_fret = calc_tendance([f['prix_usd'] for f in fret])

    # Regroupe les prix véhicules par modèle, dans l'ordre de première apparition
    # (important pour que la couleur d'un modèle reste stable dans le graphe).
    vehicules = {}
    for ligne in db.lister_vehicules():
        vehicules.setdefault(ligne['modele'], []).append(
            {'date': ligne['date'], 'prix': ligne['prix_dzd']}
        )

    return render_template(
        'marche.html',
        active='marche',
        eur_usd=eur_usd,
        fret=fret,
        tendance_fret=tendance_fret,
        vehicules=vehicules,
        aujourdhui=date.today().isoformat(),
    )


@app.route('/marche/fret', methods=['POST'])
def ajouter_fret():
    try:
        prix = float(request.form['prix_usd'])
        date_saisie = request.form.get('date') or date.today().isoformat()
        note = request.form.get('note', '').strip()
        db.ajouter_fret(date_saisie, prix, note)
    except (ValueError, KeyError):
        pass
    return redirect(url_for('marche'))


@app.route('/marche/vehicule', methods=['POST'])
def ajouter_vehicule():
    try:
        modele = request.form['modele'].strip()
        prix = float(request.form['prix_dzd'])
        date_saisie = request.form.get('date') or date.today().isoformat()
        if modele:
            db.ajouter_vehicule(date_saisie, modele, prix)
    except (ValueError, KeyError):
        pass
    return redirect(url_for('marche'))


if __name__ == '__main__':
    # host='0.0.0.0' rend l'appli accessible depuis d'autres appareils
    # sur le même réseau wifi (ex: ton smartphone) — voir le README.
    app.run(host='0.0.0.0', port=5000, debug=True)
