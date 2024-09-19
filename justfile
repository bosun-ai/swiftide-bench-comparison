wikitext_repo := "Salesforce/wikitext"
wikitext_file := "wikitext-103-v1/train-00000-of-00002.parquet"

rotten_tomatoes_repo := "cornell-movie-review-data/rotten_tomatoes"
rotten_tomatoes_file := "train.parquet"


_default:
  @just --list --unsorted

[group("data")]
download-dataset REPO FILE:
  huggingface-cli download --repo-type dataset {{REPO}} {{FILE}}

[group("benchmarks")]
run-benchmark NAME REPO FILE COLUMN RUNS="1" WARMUP="0": release-build-swiftide
  #!/usr/bin/env bash
  set -exuo pipefail
  echo "Benchmarking NAME - {{REPO}} with {{FILE}}"
  path=`just download-dataset {{REPO}} {{FILE}}`
  hyperfine  -r {{RUNS}} -w {{WARMUP}}  \
  -n langchain "cd langchain-bench && poetry run cli --dataset {{REPO}} --dataset-file $path --column-name {{COLUMN}} -q lanchain-{{NAME}}" \
  -n swiftide "cd swiftide-bench && cargo run --release -- --collection-name swiftide-{{NAME}} parquet $path {{COLUMN}}" \
  --export-markdown results/{{NAME}}.md \
  --export-json results/{{NAME}}.json

run-benchmark-swiftide-old-new NAME REPO FILE COLUMN RUNS="3" WARMUP="1": release-build-swiftide release-build-swiftide-other
  #!/usr/bin/env bash
  set -exuo pipefail
  export RUST_LOG=swiftide=debug
  echo "Benchmarking NAME - {{REPO}} with {{FILE}}"
  path=`just download-dataset {{REPO}} {{FILE}}`
  hyperfine  -r {{RUNS}} -w {{WARMUP}} -L embeddingmodel fast-embed,open-ai  \
  "cd swiftide-bench && cargo run --release -- --collection-name swiftide-{{NAME}} -e {embeddingmodel} parquet $path {{COLUMN}}" \
  "cd swiftide-bench-other && cargo run --release -- --collection-name swiftide-other-{{NAME}} -e {embeddingmodel} parquet $path {{COLUMN}}" \
  --export-markdown results/swiftide-old-new-{{NAME}}.md \
  --export-json results/swiftide-old-new-{{NAME}}.json

[group("data")]
download-rust-book:
  mkdir -p data/rust-book && \
  cd data/rust-book && \
  curl https://codeload.github.com/rust-lang/book/tar.gz/main | \
  tar -xz --strip=2 book-main/src


[group("benchmarks")]
[doc("Large dataset of 10M+ rows")]
benchmark-wikitext:
  just run-benchmark wikitext {{wikitext_repo}} {{wikitext_file}} text

[group("benchmarks")]
[doc("Medium dataset of 10k+ rows")]
benchmark-rotten-tomatoes:
  just run-benchmark rotten-tomatoes {{rotten_tomatoes_repo}} {{rotten_tomatoes_file}} text

benchmark-rotten-tomatoes-before-after:
  just run-benchmark-swiftide-old-new rotten-tomatoes {{rotten_tomatoes_repo}} {{rotten_tomatoes_file}} text

[group("benchmarks")]
[doc("Small dataset of 100 rows")]
benchmark-rust-book: download-rust-book release-build-swiftide
  hyperfine --warmup 1 -r 3 \
  -n langchain "cd langchain-bench && poetry run cli --dir rust-book -q lanchain-rust-book" \
  -n swiftide "cd swiftide-bench && cargo run --release -- --collection-name swiftide-rust-book filename rust-book" \
  --export-markdown results/rust-book.md \
  --export-json results/rust-book.json

[group("benchmarks")]
[doc("Small dataset of 100 rows")]
benchmark-rust-book-before-after: download-rust-book release-build-swiftide release-build-swiftide-other
  hyperfine -r 1 -L embeddingmodel fast-embed,open-ai --show-output \
  "cd swiftide-bench && cargo run --release -- --chunk-markdown -e {embeddingmodel} --collection-name swiftide-rust-book filename rust-book" \
  "cd swiftide-bench-other && cargo run --release -- --chunk-markdown -e {embeddingmodel} --collection-name swiftide-rust-book filename rust-book" \
  --export-markdown results/swiftide-old-new-rust-book.md \
  --export-json results/swiftide-old-new-book.json

[group("setup")]
release-build-swiftide:
  @cd swiftide-bench && cargo build --release

[group("setup")]
setup-langchain:
  @cd langchain-bench && poetry install

[group("setup")]
release-build-swiftide-other:
  @cd swiftide-bench-other && cargo build --release
