"""
Calculateur de coût d'importation véhicule (Chine -> Algérie)
--------------------------------------------------------------
Petite application Flask pour s'entraîner :
- une route ("/") qui affiche un formulaire (GET) et traite son envoi (POST)
- un calcul simple en Python pur (pas besoin de base de données pour ce V1)
- un template Jinja (index.html) qui affiche le formulaire + le résultat
"""

from flask import Flask, render_template, request

# On crée l'objet application. __name__ dit à Flask où se trouve ce fichier,
# pour qu'il sache où chercher le dossier "templates".
app = Flask(__name__)


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
    return render_template('index.html', resultat=resultat, erreur=erreur)


if __name__ == '__main__':
    # host='0.0.0.0' rend l'appli accessible depuis d'autres appareils
    # sur le même réseau wifi (ex: ton smartphone) — voir le README.
    app.run(host='0.0.0.0', port=5000, debug=True)
