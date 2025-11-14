# Predict'Mob

> [!TIP]
> En début de README, on décrit le projet, son but et son fonctionnement de manière très succinte.

## 🚀 Démarrage Rapide

### Prérequis

- Docker et Docker Compose installés
- Git

### Installation et Lancement

```bash
# 1. Copier la configuration d'environnement
cp .env.example .env

# 2. Démarrer tous les services
docker compose up -d

# 3. Vérifier les services
docker compose ps

# 4. Tester l'API
curl http://localhost:8000/health
curl http://localhost:8000/v1/alternatives
```

### 🔗 Accès aux Services

- **API Documentation** : <http://localhost:8000/docs>
- **Interface DB (Adminer)** : <http://localhost:9000>
- **Health Check** : <http://localhost:8000/health>

### 🐳 Architecture Docker

| Service | Description | Port |
|---------|-------------|------|
| **db** | PostgreSQL 15 | 5432 |
| **backend** | FastAPI API | 8000 |
| **adminer** | Interface DB | 9000 |
| **migration** | Flyway migrations | - |
| **predict-delays** | Modèle ML XGBoost (en dev) | - |

🧠 **Modèle de prédiction** : XGBoost utilisant données IDFM + météo pour prédire les retards et générer des hotspots automatiquement.

📖 **Documentation complète** : [docs/environement.md](docs/environement.md)

---

## Présentation du projet

Ce projet a été développé dans le cadre du [Hackathon Mobilités 2025](https://github.com/hackathons-mobilites/hackathon_mobilites_2025), organisé par Île-de-France Mobilités les 13 et 14 novembre 2025.

### Le problème et la proposition de valeur
>
> [!TIP]
> Ici vous pouvez répondre aux questions suivantes :
>
> - A quel problème votre projet répond-t-il ?
> - Quels sont les usagers cibles ?

### La solution
>
> [!TIP]
> Ici vous pouvez présenter
>
> - Votre solution et son fonctionnement général
> - Les données mobilisées
> - Comment elle répond au problème

### Les problèmes surmontés et les enjeux en matière de données
>
> [!TIP]
> Ici vous pouvez présenter les principaux problèmes rencontrés en les liant à vos solutions, ainsi que d'éventuelles recommendations à Ile-de-France Mobilités en matière d'ouverture de données et d'API qui auraient été utiles pour votre proposition

### Et la suite ?
>
> [!TIP]
> Ici vous vous projetez sur comment vous auriez aimé développer votre projet si vous aviez eu plus de temps ! (Quel cas d'usage pour la suite ? Quelles ressources à mobiliser ?)

## Installation et utilisation
>
> [!TIP]
> Si vous avez le temps, vous pouvez décrire les étapes d'installation de votre projet (commandes à lancer, ...) et son fonctionnement.

## La licence
>
> Ici, il faut décrire la ou les licences du projet. Vous pouvez utiliser la licence [MIT](LICENSE), qui est très permissive. Si on souhaite s'assurer que les dérivés du projet restent Open-Source, vous pouvez utiliser la licence [GPLv3](https://github.com/Illumina/licenses/blob/master/gpl-3.0.txt).

Le code et la documentation de ce projet sont sous licence [MIT](LICENSE).
