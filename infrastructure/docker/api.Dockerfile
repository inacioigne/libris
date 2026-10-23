FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN pip install --no-cache-dir uv==0.12.24

COPY libris-api/pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY libris-api/app ./app
RUN uv sync --no-dev && useradd --system --uid 10001 libris

ENV PATH="/opt/venv/bin:$PATH"

USER libris

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
