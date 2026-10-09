FROM python:3.13-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_NO_CACHE=1
RUN pip install --no-cache-dir uv==0.12.24
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY apps/api/ ./
RUN uv sync --locked --no-dev && useradd --system --uid 10001 libris
ENV PATH="/app/.venv/bin:$PATH"
USER libris
EXPOSE 8000
CMD ["uvicorn", "libris.main:app", "--host", "0.0.0.0", "--port", "8000"]
