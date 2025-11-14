# Documentation

## Variables d'environnement

### PostgreSQL

| Variable                | Description                                           | Valeur par défaut |
|-------------------------|------------------------------------------------------|-------------------|
| `POSTGRES_SERVICE_PORT` | Port d'écoute du service PostgreSQL                  | 5432              |
| `POSTGRES_DB`           | Nom de la base de données utilisée par l'application | -                 |
| `POSTGRES_USER`         | Nom d'utilisateur pour la connexion PostgreSQL       | -                 |
| `POSTGRES_PASSWORD`     | Mot de passe de l'utilisateur PostgreSQL             | -                 |

### Adminer

| Variable               | Description                           | Valeur par défaut |
|------------------------|---------------------------------------|-------------------|
| `ADMINER_SERVICE_PORT` | Port d'écoute du service Adminer      | 9000              |

---

## Guide de migration (Flyway)

Les migrations de base de données sont gérées avec l'outil **Flyway**.

### Commandes principales

| Commande   | Description                                      |
|------------|--------------------------------------------------|
| `info`     | Affiche l'état des migrations                    |
| `migrate`  | Applique les migrations non encore exécutées     |
| `clean`    | Supprime toutes les tables de la base de données |
| `validate` | Vérifie la cohérence des migrations              |

#### Exemple d'utilisation

```bash
docker compose run --rm migration <commande>
```

Remplacez `<commande>` par l'une des commandes listées ci-dessus.

---

### Création de migrations

Pour créer une migration, ajoutez un fichier SQL dans le dossier de migrations monté dans le conteneur Flyway (par exemple `./migrations`).

Flyway distingue deux types de migrations :

- **Migrations versionnées** : utilisées pour les évolutions du schéma (création/modification de tables, etc.).
  - Format de nom attendu : `V<version>__<description>.sql`
  - Exemple : `V1__init_schema.sql`, `V2__ajout_table_utilisateur.sql`

- **Migrations répétables** : utilisées pour des scripts à réappliquer à chaque changement (vues, fonctions, données de référence, etc.).
  - Format de nom attendu : `R__<description>.sql`
  - Exemple : `R__vues_metier.sql`, `R__data_reference.sql`

Placez les fichiers dans les sous-dossiers `versioned` ou `repeatable` selon la configuration de votre service Flyway.

Lors de l'exécution de la commande `migrate`, Flyway applique automatiquement les migrations versionnées non encore exécutées et réapplique les migrations répétables si leur contenu a changé.

> **Remarque importante sur les migrations répétables** :
>
> Les scripts de migration répétables doivent pouvoir être réexécutés à tout moment sans provoquer de duplication de données ou d'erreurs. Pour cela, il est recommandé d'utiliser des clauses comme `ON CONFLICT` lors des insertions (`INSERT ... ON CONFLICT DO NOTHING`), ou d'adopter une stratégie de suppression préalable des données concernées (`DELETE FROM ...` suivi d'un `INSERT`).
>
> Exemple :
>
> ```sql
> INSERT INTO reference_table (id, label) VALUES (1, 'valeur')
>   ON CONFLICT (id) DO UPDATE SET label = EXCLUDED.label;
> ```
>
> ou
>
> ```sql
> DELETE FROM reference_table;
> INSERT INTO reference_table (id, label) VALUES (1, 'valeur');
> ```

---

### Exemple de configuration `.env`

```env
# Configuration PostgreSQL
POSTGRES_SERVICE_PORT=5432
POSTGRES_DB=predictmob
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Configuration Adminer
ADMINER_SERVICE_PORT=9000
```

---

## Accès à Adminer

Adminer est une interface web permettant de gérer la base de données PostgreSQL facilement.

Après avoir démarré les services avec :

```bash
docker compose up -d
```

Accédez à Adminer via votre navigateur à l’adresse suivante :

```
http://localhost:9000
```

(Remplacez `9000` par la valeur de la variable `ADMINER_SERVICE_PORT` si vous l’avez modifiée dans votre fichier `.env`.)

- Système : `PostgreSQL`
- Serveur : `db` (ou laissez la valeur par défaut si déjà renseignée)
- Utilisateur : la valeur de `POSTGRES_USER`
- Mot de passe : la valeur de `POSTGRES_PASSWORD`
- Base de données : la valeur de `POSTGRES_DB`

Vous pouvez ainsi visualiser, modifier et administrer vos tables et données facilement