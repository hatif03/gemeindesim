FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Replace with API server once implemented; stub proves container starts.
CMD ["python", "-m", "gemeindesim"]
