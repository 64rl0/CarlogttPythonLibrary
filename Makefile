.PHONY: build
build:
	./scripts/build_venv.sh "build_venv"

.PHONY: format
format:
	./scripts/formatter.sh

.PHONY: release
release:
	./scripts/release.sh

.PHONY: deploy-pypi
deploy-pypy:
	./scripts/deploy_pypi.sh
