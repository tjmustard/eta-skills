.PHONY: validate new package catalog sync
RUN = uv run --group dev python

sync:
	uv sync --group dev

validate:
	$(RUN) tools/validate.py
	@command -v claude >/dev/null && claude plugin validate . || echo "note: claude CLI not found, skipped plugin validate"

new:
	@test -n "$(name)" || (echo "usage: make new name=<skill-name>"; exit 2)
	$(RUN) tools/new.py $(name)

package:
	@test -n "$(name)" || (echo "usage: make package name=<skill-name>"; exit 2)
	$(RUN) tools/package.py $(name)

catalog:
	$(RUN) tools/catalog.py
