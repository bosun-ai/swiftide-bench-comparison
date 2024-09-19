from typing import Required
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.utils.iter import batch_iterate
from langchain_qdrant import Qdrant
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_community.document_loaders import (
    DirectoryLoader,
    HuggingFaceDatasetLoader,
)
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.document_loaders import TextLoader

from multiprocessing import cpu_count

from argparse import ArgumentParser

parser = ArgumentParser(
    prog="Langchain Benchmark",
)

# HuggingFaceDatasetLoader
parser.add_argument("--dataset", help="Hugging face dataset name")
parser.add_argument("--dataset-file", help="Filename to use as input data")
parser.add_argument("--column-name", help="Column to use as input data")

# DirectoryLoader
parser.add_argument("--dir", help="Dataset from directory")

parser.add_argument(
    "-q", "--qdrant-collection-name", required=True, help="Qdrant collection name"
)


def main():
    args = parser.parse_args()
    print("Starting benchmark...")
    loader = get_loader(args.dataset, args.dataset_file, args.column_name, args.dir)
    run(loader, args.qdrant_collection_name)


def get_loader(dataset: str, dataset_file: str, column_name: str, dir: str):
    if dataset and column_name:
        return HuggingFaceDatasetLoader(
            dataset,
            page_content_column=column_name,
            name="default",
        )
    elif dir:
        return DirectoryLoader(
            f"../data/{dir}/",
            glob="**/*.md",
            show_progress=True,
            loader_cls=UnstructuredMarkdownLoader,
        )
    else:
        raise Exception("Could not build loader from args")


def run(loader: BaseLoader, collection_name: str):
    # FastEmbedEmbeddings
    # usage: embeddings.embed_documents(list[])
    # Wtf is with the args?
    #
    # For performance, can tune `parallel` and `threads`
    print("Setting up embeddings ...")
    embeddings = FastEmbedEmbeddings(
        cache_dir=None, threads=None, model_name="BAAI/bge-small-en-v1.5", _model=None
    )

    # Dataset loader
    print("Setting up loader ...")
    # documents = sum(
    #     map(lambda d: d.page_content, loader.alazy_load()),
    #     [],
    # )

    # print(f"Embedding {len(documents)} chunks ...")
    #
    # Qdrant
    # Can this even be async?
    print("Initializing qdrant client ...")
    client = QdrantClient()
    aclient = AsyncQdrantClient()

    print("Creating qdrant collection ...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    print("Creating langchain vector store ...")
    vector_store = Qdrant(
        client=client,
        async_client=aclient,
        collection_name=collection_name,
        embeddings=embeddings,
    )

    print("Async adding documents to vector store ...")
    batch_size = 4
    # Batch over lazy loader
    batch_count = 1
    for batch in batch_iterate(iterable=loader.lazy_load(), size=batch_size):
        print(f"Processing batch {batch_count} ...")
        vector_store.add_documents(batch)
        batch_count += 1

    print("Getting qdrant collection statistics ...")
    collection = client.get_collection(collection_name)

    print(f"Added vectors: {collection.vectors_count}")
