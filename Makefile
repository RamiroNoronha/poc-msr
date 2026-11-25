VENV := .venv
BIN := $(VENV)/bin

.PHONY: dev start install lint format

# Instala as dependências do projeto
install:
	python3 -m venv $(VENV)
	$(BIN)/pip install -r requirements.txt

# Sobe o servidor em modo desenvolvimento (com hot-reload)
dev:
	$(BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Sobe o servidor em modo produção
start:
	$(BIN)/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Formata o código com ruff
format:
	$(BIN)/ruff format .

# Verifica erros de lint com ruff
lint:
	$(BIN)/ruff check .
