PYTHON = python
SCRIPT = ./src/downloader.py
CSV_FILE ?= ./input/input_links.csv
OUT_DIR ?= ./output/downloaded_files
BROWSER ?= chrome

.PHONY: help install run clean

help:
	@echo "Available commands:"
	@echo "  make install       Install required Python dependencies"
	@echo "  make run           Run the downloader script"
	@echo "  make clean         Remove the output directory"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) $(SCRIPT) $(CSV_FILE) $(OUT_DIR) --browser $(BROWSER)

clean:
	rm -rf $(OUT_DIR)