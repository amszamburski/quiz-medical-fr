# Quiz Médical Français

Application web de quiz médical avec deux modes de concours : national (par équipe CHU) et personnel (par sujet).

## Fonctionnalités

### 🏥 Concours National
- Sélection d'équipe CHU (26 villes françaises)
- 5 questions aléatoires sur tous les sujets médicaux
- Classement par équipe en temps réel (top 3)
- Remise à zéro quotidienne automatique

### 👨‍⚕️ Concours Personnel
- Sélection par sujet médical spécialisé
- 5 questions ciblées sur le sujet choisi
- Score personnel avec feedback détaillé
- Contenu éducatif avec références scientifiques

### 🤖 Génération IA de Questions
- Vignettes cliniques réalistes générées par GPT-4o
- Questions à réponse libre
- Évaluation automatique des réponses
- Feedback personnalisé et contenu éducatif

## Installation

### Prérequis
- Python 3.8+
- Clé API OpenAI
- Redis (optionnel, sinon SQLite en fallback)

### Configuration

1. **Cloner et installer les dépendances :**
```bash
cd quiz-medical-fr
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
```

2. **Configurer les variables d'environnement :**
```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

Variables requises :
- `OPENAI_API_KEY` : Votre clé API OpenAI (obligatoire)
- `SECRET_KEY` : Clé secrète Flask pour les sessions
- `REDIS_URL` : URL Redis (optionnel, SQLite par défaut)

3. **Mettre à jour les recommandations depuis un fichier Excel (.xls/.xlsx) :**
```bash
# Activez l'environnement virtuel si besoin
source venv/bin/activate

# Convertir le nouveau fichier Excel vers CSV utilisé par l'app
python scripts/update_recommendations.py /chemin/vers/nouveau_fichier.xls --sheet 0

# Par défaut, le CSV est écrit dans data/recommendations.csv (backup auto)
```

Notes:
- Le script accepte .xls et .xlsx. Les dépendances nécessaires (`openpyxl` et `xlrd==1.2.0`) sont listées dans `requirements.txt`.
- Le script tente d'apparier automatiquement les colonnes attendues: Theme/Topic/Recommendation/Grade/Evidence/References/Link (les alias français sont supportés: Thème, Sujet, Recommandation, Preuves, Références, Lien).
- Les lignes sans Recommendation ou Evidence sont ignorées (aligné avec la logique de l'app).

## Utilisation

### Démarrage en développement
```bash
source venv/bin/activate
python run_local.py
```

L'application sera accessible sur http://localhost:5001

### Structure des données

Le fichier `data/Recommendations_source.xlsx` contient les recommandations médicales avec :
- **Theme** : Thème médical
- **Topic** : Sujet spécifique
- **Recommendation** : Recommandation clinique
- **Grade** : Grade de recommandation
- **Evidence** : Preuves scientifiques
- **References** : Références bibliographiques

## Architecture

```
app/
├── routes/           # Routes Flask
│   ├── main.py      # Page d'accueil
│   ├── national.py  # Concours national
│   └── personal.py  # Concours personnel
├── utils/           # Utilitaires
│   ├── constants.py # Constantes (équipes CHU, etc.)
│   ├── db.py        # Chargement des données CSV
│   ├── openai_client.py # Client OpenAI avec retry
│   ├── prompts.py   # Prompts pour GPT-4o
│   ├── vignette.py  # Génération de vignettes
│   ├── scorer.py    # Évaluation des réponses
│   └── scoreboard.py # Système de classement
└── templates/       # Templates Jinja2
```

## API OpenAI

L'application utilise GPT-4o pour :

1. **Génération de vignettes** : Création de cas cliniques réalistes
2. **Évaluation de réponses** : Notation sur 20 avec feedback
3. **Contenu éducatif** : Explications avec références scientifiques

## Base de données

- **Redis** : Classement temps réel (production)
- **SQLite** : Fallback automatique (développement)
- **CSV** : Recommandations médicales (statique)

## Équipes CHU disponibles

26 CHU français : Amiens, Angers, Besançon, Bordeaux, Brest, Caen, Clermont-Ferrand, Dijon, Grenoble, Lille, Limoges, Lyon, Marseille, Montpellier, Nancy, Nantes, Nice, Paris, Poitiers, Reims, Rennes, Rouen, Saint-Étienne, Strasbourg, Toulouse, Tours.

## Sujets médicaux disponibles

Basés sur les données CSV :
- Trauma abdominal
- Trauma crânien
- Trauma des membres
- Trauma thoracique
- Trauma vertébro-médullaire

## Déploiement

### Vercel (recommandé)
1. Connecter le repo GitHub à Vercel
2. Ajouter les variables d'environnement dans le dashboard
3. Configurer Redis via Upstash (optionnel)

### Docker
```bash
# À venir - Dockerfile à créer
```

## Développement

### Tests
```bash
source venv/bin/activate
pytest tests/
```

### Linting
```bash
source venv/bin/activate
black app/
flake8 app/
```

## License

MIT License - Voir LICENSE pour plus de détails.

## Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request
