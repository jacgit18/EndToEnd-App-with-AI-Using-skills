FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependencies first, so a code change doesn't reinstall the world.
COPY pyproject.toml ./
RUN uv sync

COPY . .

EXPOSE 8000

# Apply migrations, then serve with autoreload (source is bind-mounted in compose).
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
