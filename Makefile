.PHONY: api broker dashboard up down update_candles capture_signal

api:
	uvicorn services.inference_api.main:app --reload --host 0.0.0.0 --port 8080

broker:
	uvicorn services.paper_broker.main:app --reload --host 0.0.0.0 --port 8081

dashboard:
	streamlit run services/dashboard/app.py --server.port 8501 --server.address 0.0.0.0

update_candles:
	python cli/update_polygon.py --out $${DATA_DIR:-./data/market_candles} --symbol $${SYMBOL:-GBPUSD}

capture_signal:
	python cli/signal_report.py

up:
	docker compose up --build

down:
	docker compose down -v

.PHONY: test
test:
	pytest -q

.PHONY: bench
bench:
	python -m benchmarks.backtest_bench

.PHONY: tf
tf:
	cd infra/terraform && terraform fmt -check && terraform init -backend=false && terraform validate && terraform plan
