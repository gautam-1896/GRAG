PYTHON := python
VENV := .venv

.PHONY: install run serve docker test clean

install:
	$(PYTHON) -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	$(PYTHON) app.py

serve:
	$(PYTHON) -m uvicorn server:app --host 0.0.0.0 --port 8000

docker:
	docker build -t grag-app .

test:
	$(PYTHON) -m pytest -q

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
