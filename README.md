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

## Use cases
- добавить 1 компанию
- добавить сразу несколько компаний
- проанализировать 1 компанию
- проанализировать сразу несколько компаний (по списку id, по городу, по отрасли, все)
- получить список компаний с данными по последней дате (с фильтром GET /companies)
- получить поля и список данных конкретной компании (упорядоченный по дате в порядке убывания)
- удалить компанию
- удалить данные компании (все или с фильтром по id)
- изменить поля компании

## TODO:
- cms, language, framework, external_js, social_links вынести в отдельную таблицу companies_data, связанную с companies по ключу, добавить поле date_parse (Date)
- добавить метод POST /companies, который добавит запись(и) в таблицу companies
- изменить метод POST /analyze на POST /companies/analyze - метод должен запускать Main.process для компании с фильтром по списку id, по городу, по отрасли
- метод Main.process должен сохранять новую запись в таблице companies_data
- изменить метод GET /companies, чтобы он возвращал данные по послдней дпте
- добавить в метод GET /companies фильтр по городу, отрасли
- удалить метод /companies/{city}/{industry}/{company_name}
- добавить метод GET /companies/{id} возвращающий поля и список данных конкретной компании (упорядоченный по дате в порядке убывания)
- добавить метод DELETE /companies/{id}/data/{data_id}
- добавить метод DELETE /companies/{id}/data
- добавить метод DELETE /companies/{id}
- добавить метод PATCH /companies/{id}