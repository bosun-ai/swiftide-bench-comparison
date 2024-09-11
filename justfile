download-wikitest := `huggingface-cli download --repo-type dataset Salesforce/wikitext  wikitext-103-v1/train-00000-of-00002.parquet`

benchmark-wikitest:
  echo {{ download-wikitest }}

download-rust-book:
  mkdir -p data/rust-book && \
  cd data/rust-book && \
  curl https://codeload.github.com/rust-lang/book/tar.gz/main | \
  tar -xz --strip=2 book-main/src

benchmark-rust-book: download-rust-book
  hyperfine -w 1 \
  -n langchain "cd langchain-bench && poetry run cli --dir rust-book -q lanchain-rust-book" \
  -n swiftide "cd swiftide-bench && cargo run --release -- -d rust-book -c swiftide-rust-book"

  
