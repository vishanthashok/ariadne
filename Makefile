.PHONY: setup download-data process-data train evaluate serve-api serve-frontend demo docker-up generate-demo test

PYTHON ?= python
PIP ?= pip

setup:
	$(PIP) install -r requirements.txt
	cd frontend && npm install

download-data:
	$(PYTHON) -m data.scripts.download_sentinel

process-data:
	$(PYTHON) -m data.scripts.slice_patches
	$(PYTHON) -m data.scripts.generate_drone_views
	$(PYTHON) -m data.scripts.build_faiss_index
	$(PYTHON) -m data.scripts.generate_imu_data

train:
	$(PYTHON) -m model.train --epochs 5 --batch-size 16

evaluate:
	$(PYTHON) -m model.evaluate

serve-api:
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

serve-frontend:
	cd frontend && npm run dev

demo: generate-demo
	@echo "Demo data ready. Start frontend with: make serve-frontend"
	@echo "Or full stack: make serve-api (separate terminal) + make serve-frontend"

generate-demo:
	$(PYTHON) -m api.generate_demo

docker-up:
	docker compose up --build

test:
	$(PYTHON) -m pytest tests/ -q
	cd frontend && npm run build
