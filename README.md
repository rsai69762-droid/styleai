# StylAI

Monorepo de l'application StylAI : recommandation de tenues personnalisées.

## Structure du projet

```
stylai/
├── apps/
│   ├── api/        # Backend FastAPI (Python 3.11+)
│   └── web/        # Frontend Next.js 16 (React 19)
├── packages/
│   └── scraper/    # Pipeline de scraping
├── infra/
│   └── docker-compose.yml   # Postgres (pgvector) + api + web
└── .env.example
```

## Pré-requis

- **Docker** et **Docker Compose**
- **Python 3.11+** (pour exécuter l'API en local hors Docker)
- **Node.js 20+** et **pnpm** (pour exécuter le web en local hors Docker)
- **Ollama** (optionnel) si vous utilisez le provider LLM local

## Variables d'environnement

Trois fichiers `.env` sont attendus :

| Fichier | Rôle |
|---|---|
| `infra/.env` | Variables consommées par `docker-compose` (Postgres, builds Next.js) |
| `apps/api/.env` | Configuration de l'API (DB, LLM, Supabase) |
| `apps/web/.env.local` | Variables publiques Next.js |

Un modèle est fourni à la racine : [.env.example](.env.example). Copiez-le vers chacun des emplacements ci-dessus et complétez les valeurs.

```bash
cp .env.example infra/.env
cp .env.example apps/api/.env
cp .env.example apps/web/.env.local
```

> Les variables seront ajoutées dans la pipeline de déploiement par la suite.

### Variables principales

- `DB_PASSWORD`, `DATABASE_URL` — connexion Postgres
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — authentification Supabase
- `OLLAMA_BASE_URL` — URL du serveur Ollama local
- `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` — provider Anthropic (alternatif à Ollama)
- `LLM_PROVIDER` — `ollama` ou `anthropic`
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` — front Next.js

## Démarrage rapide (Docker Compose)

Lance Postgres + API + Web en une commande :

```bash
cd infra
docker compose up --build
```

Services exposés :

- Web : http://localhost:3000
- API : http://localhost:8000 (docs : http://localhost:8000/docs)
- Postgres : `localhost:5434` (user `stylai`, db `stylai`)

Pour arrêter :

```bash
docker compose down
```

Pour réinitialiser la base (supprime le volume) :

```bash
docker compose down -v
```

## Démarrage en local (développement)

### 1. Postgres uniquement via Docker

```bash
cd infra
docker compose up postgres
```

### 2. API (FastAPI)

```bash
cd apps/api

# Créer l'environnement virtuel
python3.11 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -e ".[dev]"

# Appliquer les migrations
alembic upgrade head

# Lancer l'API en mode dev
uvicorn src.main:app --reload --port 8000
```

API disponible sur http://localhost:8000 — documentation OpenAPI sur http://localhost:8000/docs.

### 3. Web (Next.js)

```bash
cd apps/web
pnpm install
pnpm dev
```

Front disponible sur http://localhost:3000.

### 4. Ollama (optionnel)

Si `LLM_PROVIDER=ollama` :

```bash
# Installer Ollama : https://ollama.com
ollama pull qwen3:8b
ollama serve
```

## Migrations base de données

Les migrations Alembic se trouvent dans [apps/api/alembic/versions/](apps/api/alembic/versions/).

```bash
cd apps/api

# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Appliquer
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

## Tests & qualité

```bash
# API
cd apps/api
pytest
ruff check src/

# Web
cd apps/web
pnpm lint
```

## Dépannage

- **Port 5434 déjà utilisé** : modifiez le mapping dans [infra/docker-compose.yml](infra/docker-compose.yml).
- **L'API ne se connecte pas à Postgres en Docker** : vérifiez que `DATABASE_URL` pointe vers `postgres` (et non `localhost`) dans `apps/api/.env` lorsqu'elle tourne en conteneur.
- **Ollama injoignable depuis Docker** : le compose utilise `host.docker.internal:11434` — assurez-vous qu'Ollama écoute bien sur l'hôte.


## Accès à la base de données

Postgres tourne dans le conteneur `stylai-db` et est exposé sur le port hôte **5434** (mappé vers `5432` côté conteneur). Voir [infra/docker-compose.yml](infra/docker-compose.yml).

### Connexion depuis l'hôte (psql)

```bash
# avec mot de passe interactif
psql -h localhost -p 5434 -U stylai -d stylai
# mot de passe : stylai_dev_password (ou la valeur de DB_PASSWORD)
```

Ou en une seule ligne avec une URL de connexion :

```bash
psql "postgresql://stylai:stylai_dev_password@localhost:5434/stylai"
```

### Connexion depuis l'intérieur du conteneur

```bash
docker exec -it stylai-db psql -U stylai -d stylai
```

### Clients GUI (TablePlus, DBeaver, pgAdmin, DataGrip…)

| Champ      | Valeur                  |
|------------|-------------------------|
| Host       | `localhost` (`127.0.0.1`) |
| Port       | `5434`                  |
| Database   | `stylai`                |
| User       | `stylai`                |
| Password   | `stylai_dev_password`   |

### Commandes psql utiles

```sql
\dt              -- lister les tables
\d products      -- décrire une table
\dx              -- lister les extensions (vérifier la présence de "vector" pour pgvector)
SELECT count(*) FROM products;
```

### Installer psql si nécessaire

```bash
brew install libpq && brew link --force libpq
# ou
brew install postgresql@16
```