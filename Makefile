# pattern-synthesis workflow
CORPUS := data/sjonabok/patterns/txt
OUT    := out

.PHONY: all data stats review preview clean

all: stats review

data:
	git submodule update --init --recursive

$(OUT):
	mkdir -p $@

stats: data | $(OUT)
	scripts/corpus-stats.sh $(CORPUS) > $(OUT)/corpus-stats.tsv
	@echo "wrote $(OUT)/corpus-stats.tsv"

review:
	quarto render review

preview:
	quarto preview review

clean:
	rm -rf out review/_book review/.quarto
