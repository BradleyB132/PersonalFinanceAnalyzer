FROM python:3.11-slim

RUN pip install poetry==1.8.2

WORKDIR /app

# Copy dependency metadata first so Docker can cache installs across code changes.
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
