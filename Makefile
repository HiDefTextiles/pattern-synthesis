# pattern-synthesis workflow
CORPUS := data/sjonabok/patterns/min
OUT    := out

.PHONY: help setup all data stats banners banner clear frame compare review docs-data docs docs-preview docs-clean preview clean

help:           ## list the targets (default)
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/' | expand -t 16

setup: data     ## fetch the Sjónabók corpus and install the Python packages
	python3 -m pip install -r requirements.txt

all: stats review

data:
	git submodule update --init --recursive

$(OUT):
	mkdir -p $@

stats: data | $(OUT)  ## corpus sizes and fill ratios -> out/corpus-stats.tsv
	scripts/corpus-stats.sh $(CORPUS) > $(OUT)/corpus-stats.tsv
	@echo "wrote $(OUT)/corpus-stats.tsv"

banners: data | $(OUT)  ## prototype banners, all presets -> out/banners/
	python3 python/banner.py --preset all --slots 9 --far 1000 --out $(OUT)/banners

# One knitted piece with the full version-1 output set (settings: banner.yml)
SEED ?= 1
FIRST ?= 0
banner: data | $(OUT)  ## one knitted piece with all outputs (SEED=1 FIRST=0) -> out/banner-*/
	python3 python/make_banner.py --seed $(SEED) --first $(FIRST) --out $(OUT)/banner-seed$(SEED)-from$(FIRST)

# Post-processing step on the motifs: dotted templates with the clear space marked
RING ?= 1
clear: data | $(OUT)  ## motif templates with empty space as '.' (RING=1) -> out/clear/
	python3 python/clear_space.py --ring $(RING) --out $(OUT)/clear

# Frames from four border bands with a corner connector
BAND ?= thjms1105_38_p2
NX ?= 4
NY ?= 3
CORNER ?= mitre
CUT ?= best
frame: data | $(OUT)  ## a frame from one band (BAND= NX= NY= CORNER=mitre|motif|grown|all, default mitre CUT=best|stored) -> out/frame-*/
	python3 python/frame.py --band $(BAND) --nx $(NX) --ny $(NY) --corner $(CORNER) --cut $(CUT) --seed $(SEED) --out $(OUT)/frame-$(BAND)

compare: data | $(OUT)  ## compare the fill methods -> out/compare/
	python3 python/banner.py --filler compare --slots 4 --out $(OUT)/compare
	python3 python/compare_fillers.py 4

review:         ## render the literature review -> review/_book/
	quarto render review

preview:
	quarto preview review

# ── Docs website (site/, Quarto, same look as the Sjonabok gallery) ──────────
# make docs-data    : generate the comparison banners (site/data/banners.json)
# make docs         : render the site, then the literature review into site/_site/review
# make docs-preview : live preview of the site
DOCS_DATA = site/data/banners.json

$(DOCS_DATA): python/explainer_data.py python/clear_space.py python/banner.py python/fillers.py python/wfc.py python/sjonabok.py
	mkdir -p site/data
	python3 python/explainer_data.py 20 > $@

FRAMES_DATA = site/data/frames/frames.json

$(FRAMES_DATA): python/frame.py python/fillers.py python/sjonabok.py
	python3 python/frame.py --site site/data/frames

docs-data: data $(DOCS_DATA) $(FRAMES_DATA)

docs: docs-data  ## build the docs website -> site/_site/
	cd site && quarto render
	rm -rf review/_theme && mkdir -p review/_theme/img && cp -r site/styles review/_theme/ && cp -r site/img/hi review/_theme/img/
	quarto render review --profile site --to html --output-dir ../site/_site/review

docs-preview: docs-data  ## live preview of the docs website
	cd site && quarto preview

docs-clean:
	rm -rf site/_site site/.quarto site/data

clean:          ## remove generated files
	rm -rf out review/_book review/.quarto
