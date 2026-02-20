VENV_DIR ?= .venv
SYSTEM_PYTHON := /usr/bin/python3

.PHONY: install clean reinstall run

install: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate:
	$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install geopy requests matplotlib numpy black

clean:
	rm -rf $(VENV_DIR)

reinstall: clean install

run: install
	$(VENV_DIR)/bin/python -B example.py

run2: install
	$(VENV_DIR)/bin/python -B example_peak_finder.py
