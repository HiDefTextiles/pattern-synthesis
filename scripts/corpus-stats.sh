#!/bin/sh
# Print width, height and fill ratio of every Sjónabók matrix as TSV.
# Usage: scripts/corpus-stats.sh [dir]   (default: data/sjonabok/patterns/min)
dir=${1:-data/sjonabok/patterns/min}
printf 'file\twidth\theight\tones\n'
for f in "$dir"/*.txt; do
  awk -v f="$(basename "$f")" '
    NF { if (!w) w = length($0); h++; ones += gsub(/1/, "1") }
    END { printf "%s\t%d\t%d\t%.3f\n", f, w, h, ones / (w * h) }' "$f"
done
