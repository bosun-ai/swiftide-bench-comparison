| Command | Mean [s] | Min [s] | Max [s] | Relative |
|:---|---:|---:|---:|---:|
| `cd swiftide-bench && cargo run --release -- --chunk-markdown -e fast-embed --collection-name swiftide-rust-book filename rust-book` | 107.884 | 107.884 | 107.884 | 25.67 |
| `cd swiftide-bench-other && cargo run --release -- --chunk-markdown -e fast-embed --collection-name swiftide-rust-book filename rust-book` | 43.103 | 43.103 | 43.103 | 10.26 |
| `cd swiftide-bench && cargo run --release -- --chunk-markdown -e open-ai --collection-name swiftide-rust-book filename rust-book` | 4.202 | 4.202 | 4.202 | 1.00 |
| `cd swiftide-bench-other && cargo run --release -- --chunk-markdown -e open-ai --collection-name swiftide-rust-book filename rust-book` | 6.352 | 6.352 | 6.352 | 1.51 |
