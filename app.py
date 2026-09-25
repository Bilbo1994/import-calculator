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


def calculer_scenario(nom, taux_eur_usd, taux_eur_dzd, prix_usd, transport_usd,
                      frais_douane, nombre):
    """Coût d'un lot de voitures pour un taux euro->dollar donné."""
    # Les deux taux sont en euro : 1 USD = (EUR->DZD) / (EUR->USD) dinars
    taux_usd_dzd = taux_eur_dzd / taux_eur_usd

    voitures_usd = prix_usd * nombre
    total_usd = voitures_usd + transport_usd  # le conteneur est payé une seule fois
    douane_totale = frais_douane * nombre  # frais saisis pour une seule voiture

    sans_douane_dzd = total_usd * taux_usd_dzd
    avec_douane_dzd = sans_douane_dzd + douane_totale
    sans_douane_eur = total_usd / taux_eur_usd

    return {
        'nom': nom,
        'taux_eur_usd': taux_eur_usd,
        'taux_usd_dzd': taux_usd_dzd,
        'voitures_dzd': voitures_usd * taux_usd_dzd,
        'transport_dzd': transport_usd * taux_usd_dzd,
        'douane_dzd': douane_totale,
        'sans_douane_dzd': sans_douane_dzd,
        'sans_douane_par_voiture_dzd': sans_douane_dzd / nombre,
        'avec_douane_dzd': avec_douane_dzd,
        'avec_douane_par_voiture_dzd': avec_douane_dzd / nombre,
        'sans_douane_eur': sans_douane_eur,
        'sans_douane_par_voiture_eur': sans_douane_eur / nombre,
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    resultat = None
    erreur = None
    valeurs = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        try:
            prix_usd = float(request.form['prix_usd'])
            transport_usd = float(request.form['transport_usd'])
            taux_bon = float(request.form['taux_eur_usd_bon'])
            taux_faible = float(request.form['taux_eur_usd_faible'])
            taux_eur_dzd = float(request.form['taux_eur_dzd'])
            frais_douane = float(request.form['frais_douane'])
            nombre = int(request.form['nombre'])

            if nombre < 1 or min(taux_bon, taux_faible, taux_eur_dzd) <= 0:
                raise ValueError

            resultat = {
                'nombre': nombre,
                'frais_douane_unitaire': frais_douane,
                'scenarios': [
                    calculer_scenario('Bon taux', taux_bon, taux_eur_dzd, prix_usd,
                                      transport_usd, frais_douane, nombre),
                    calculer_scenario('Taux faible', taux_faible, taux_eur_dzd, prix_usd,
                                      transport_usd, frais_douane, nombre),
                ],
            }
        except (ValueError, KeyError):
            erreur = "Merci de remplir tous les champs avec des nombres valides (taux > 0, au moins 1 voiture)."

    return render_template(
        'index.html', resultat=resultat, erreur=erreur, valeurs=valeurs, active='calc'
    )


@app.template_filter('ecart')
def formater_ecart(valeur, decimales=0):
    if round(valeur, decimales) == 0:
        return "0"
    return f"{valeur:+,.{decimales}f}".replace(",", " ")


@app.template_filter('nombre')
def formater_nombre(valeur, decimales=0):
    return f"{valeur:,.{decimales}f}".replace(",", " ")


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
