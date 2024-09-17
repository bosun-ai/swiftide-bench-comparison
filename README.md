Swiftide benchmarks and comparisons
=======

## Installation

Install the following prerequisites:

  - [just](https://github.com/casey/just)
  - [huggingface-cli](https://huggingface.co/docs/huggingface_hub/en/guides/cli)
  - [hyperfine](https://github.com/sharkdp/hyperfine)
  - [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)

Then run `just setup-langchain` to install the necessary Python dependencies.

## Usage

Run `just` to get a list of benchmarks to run. For example to run the medium sized benchmark run `just benchmark-rotten-tomatoes`.
