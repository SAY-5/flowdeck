.PHONY: proto proto-py proto-ts lint test e2e build clean

proto: proto-py proto-ts

proto-py:
	cd apps/api && python -m grpc_tools.protoc \
		-I../../proto \
		--python_out=flowdeck/gen \
		--pyi_out=flowdeck/gen \
		--grpc_python_out=flowdeck/gen \
		../../proto/flow.proto
	@touch apps/api/flowdeck/gen/__init__.py

proto-ts:
	cd apps/web && npx buf generate ../../proto

lint:
	cd apps/api && ruff check . && black --check .
	cd apps/web && npm run lint

test:
	cd apps/api && pytest
	cd apps/web && npm run test

e2e:
	cd apps/web && npm run test:e2e

build:
	docker compose build

clean:
	rm -rf apps/api/flowdeck/gen apps/web/src/gen
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
