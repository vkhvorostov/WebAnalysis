## Usage:

### Database Migrations:

Before running the application, you need to run database migrations:

```bash
# Apply all pending migrations
alembic upgrade head

# Or use the helper script
python run_migrations.py upgrade

# Create a new migration (after modifying models)
alembic revision --autogenerate -m "description of changes"
python run_migrations.py revision "description" --autogenerate

# View migration history
alembic history

# Check current database revision
alembic current
```

### Run locally:

1. Set up environment variables (or use defaults):
   ```bash
   export POSTGRES_DB=webanalysis
   export POSTGRES_USER=exampleuser
   export POSTGRES_PASSWORD=examplepwd
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

3. Start the API:
   ```bash
   uvicorn app:app --reload
   ```

### Run with Docker Compose:

```bash
docker-compose up
```

Migrations will run automatically on startup. The API will be available at http://localhost:8000 with interactive docs at http://localhost:8000/docs.
