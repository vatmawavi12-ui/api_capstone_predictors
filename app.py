from flask import Flask, request, jsonify 
import joblib
import pandas as pd
import numpy as np
from flask_cors import CORS
import os
import math

app = Flask(__name__)
CORS(app)

MODELS_PATH = 'models/'

try:
    print("🔄 Chargement des modèles...")
    model = joblib.load(os.path.join(MODELS_PATH, 'best_model.joblib'))
    encoder = joblib.load(os.path.join(MODELS_PATH, 'encoder.joblib'))
    imputer = joblib.load(os.path.join(MODELS_PATH, 'imputer.joblib'))
    scaler = joblib.load(os.path.join(MODELS_PATH, 'scaler.joblib'))
    print("✅ Modèles chargés avec succès!")
    
    # Features du modèle (24 features numériques)
    MODEL_FEATURES = [
        'surface_m2', 'nb_chambres', 'nb_salons', 'nb_sdb', 
        'quartier_encoded', 'latitude', 'longitude', 
        'dist_centre_ville_km', 'dist_aeroport_km', 'dist_plage_km', 
        'nb_ecoles_1km', 'nb_mosquees_1km', 'nb_commerce_1km', 
        'nb_hopitaux_1km', 'nb_total_pois_1km', 'nb_pieces_total', 
        'has_garage', 'has_jardin', 'has_piscine', 'has_balcon', 
        'has_meuble', 'has_titre_foncier', 'est_neuf', 'age_annonce'
    ]
    
    print(f"📊 Features du modèle ({len(MODEL_FEATURES)}): {MODEL_FEATURES}")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    exit(1)

def prepare_features(data):
    """
    Prépare les caractéristiques pour la prédiction
    Le frontend envoie déjà toutes les features calculées
    """
    # Calcul du nombre total de pièces (si non fourni)
    if 'nb_pieces_total' not in data:
        nb_pieces_total = int(data.get('nb_chambres', 0)) + int(data.get('nb_salons', 0))
    else:
        nb_pieces_total = int(data['nb_pieces_total'])
    
    # Création du DataFrame avec les features numériques
    features_dict = {
        'surface_m2': float(data['surface_m2']),
        'nb_chambres': int(data['nb_chambres']),
        'nb_salons': int(data['nb_salons']),
        'nb_sdb': int(data['nb_sdb']),
        'quartier_encoded': float(data['quartier_encoded']),
        'latitude': float(data['latitude']),
        'longitude': float(data['longitude']),
        'dist_centre_ville_km': float(data['dist_centre_ville_km']),
        'dist_aeroport_km': float(data['dist_aeroport_km']),
        'dist_plage_km': float(data['dist_plage_km']),
        'nb_ecoles_1km': int(data['nb_ecoles_1km']),
        'nb_mosquees_1km': int(data['nb_mosquees_1km']),
        'nb_commerce_1km': int(data['nb_commerce_1km']),
        'nb_hopitaux_1km': int(data['nb_hopitaux_1km']),
        'nb_total_pois_1km': int(data['nb_total_pois_1km']),
        'nb_pieces_total': nb_pieces_total,
        'has_garage': int(data['has_garage']),
        'has_jardin': int(data['has_jardin']),
        'has_piscine': int(data['has_piscine']),
        'has_balcon': int(data['has_balcon']),
        'has_meuble': int(data['has_meuble']),
        'has_titre_foncier': int(data['has_titre_foncier']),
        'est_neuf': int(data['est_neuf']),
        'age_annonce': int(data['age_annonce'])
    }
    
    # Création du DataFrame avec l'ordre exact des features
    features = pd.DataFrame([features_dict])
    features = features[MODEL_FEATURES]
    
    return features

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Aucune donnée fournie'}), 400
        
        # Validation des champs requis
        required_fields = [
            'surface_m2', 'nb_chambres', 'nb_salons', 'nb_sdb',
            'quartier_encoded', 'latitude', 'longitude',
            'dist_centre_ville_km', 'dist_aeroport_km', 'dist_plage_km',
            'nb_ecoles_1km', 'nb_mosquees_1km', 'nb_commerce_1km',
            'nb_hopitaux_1km', 'nb_total_pois_1km',
            'has_garage', 'has_jardin', 'has_piscine', 'has_balcon',
            'has_meuble', 'has_titre_foncier', 'est_neuf', 'age_annonce'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': f'Champs manquants: {missing_fields}',
                'required_fields': required_fields
            }), 400
        
        # Préparation des features
        features = prepare_features(data)
        
        # Application des préprocesseurs
        features_imputed = imputer.transform(features)
        features_scaled = scaler.transform(features_imputed)
        
        # Prédiction (le modèle prédit log_prix)
        prediction_log = model.predict(features_scaled)[0]
        
        # Conversion du log_prix en prix réel
        prix_reel = math.exp(prediction_log)
        
        # Arrondir à l'entier le plus proche
        prix_reel_arrondi = round(prix_reel)
        
        response = {
            'success': True,
            'prix_estime': prix_reel_arrondi,
            'prix_format': f"{prix_reel_arrondi:,}".replace(',', ' '),
            'unite': 'MRU (Ouguiya)'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

