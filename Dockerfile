FROM python:3.13-slim

# O backend executa o git para clonar e minerar os repositórios.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# Um worker só: o cache dos clones e a fila de mineração ficam na memória do processo.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
