# pattern-synthesis workflow
CORPUS := data/sjonabok/patterns/txt
OUT    := out

.PHONY: all data stats banners compare explainer review preview clean

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

compare: data | $(OUT)
	python3 python/banner.py --filler compare --slots 4 --out $(OUT)/compare
	python3 python/compare_fillers.py 4

explainer: data
	python3 python/explainer_data.py 20 > docs/explainer/banners.json

review:
	quarto render review

preview:
	quarto preview review

clean:
	rm -rf out review/_book review/.quarto
