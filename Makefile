# pattern-synthesis workflow
CORPUS := data/sjonabok/patterns/txt
OUT    := out

.PHONY: all data stats banners banner compare review docs-data docs docs-preview docs-clean preview clean

all: stats review

data:
	git submodule update --init --recursive

$(OUT):
	mkdir -p $@

stats: data | $(OUT)
	scripts/corpus-stats.sh $(CORPUS) > $(OUT)/corpus-stats.tsv
	@echo "wrote $(OUT)/corpus-stats.tsv"

banners: data | $(OUT)
	python3 python/banner.py --preset all --slots 9 --far 1000 --out $(OUT)/banners

# One knitted piece with the full version-1 output set (settings: banner.yml)
SEED ?= 1
FIRST ?= 0
banner: data | $(OUT)
	python3 python/make_banner.py --seed $(SEED) --first $(FIRST) --out $(OUT)/banner-seed$(SEED)-from$(FIRST)

compare: data | $(OUT)
	python3 python/banner.py --filler compare --slots 4 --out $(OUT)/compare
	python3 python/compare_fillers.py 4

review:
	quarto render review

preview:
	quarto preview review

# ── Docs website (site/, Quarto, same look as the Sjonabok gallery) ──────────
# make docs-data    : generate the comparison banners (site/data/banners.json)
# make docs         : render the site, then the literature review into site/_site/review
# make docs-preview : live preview of the site
DOCS_DATA = site/data/banners.json

$(DOCS_DATA): python/explainer_data.py python/banner.py python/fillers.py python/wfc.py python/sjonabok.py
	mkdir -p site/data
	python3 python/explainer_data.py 20 > $@

docs-data: data $(DOCS_DATA)

docs: docs-data
	cd site && quarto render
	quarto render review --to html --output-dir ../site/_site/review

docs-preview: docs-data
	cd site && quarto preview

docs-clean:
	rm -rf site/_site site/.quarto site/data

clean:
	rm -rf out review/_book review/.quarto
