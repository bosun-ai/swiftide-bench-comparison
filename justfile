download-rust-book:
  mkdir -p data/rust-book && \
  cd data/rust-book && \
  curl https://codeload.github.com/rust-lang/book/tar.gz/main | \
  tar -xz --strip=2 book-main/src
