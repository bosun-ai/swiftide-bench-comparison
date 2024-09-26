from typing import Required
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.utils.aiter import abatch_iterate
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

import uvloop
import asyncio

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
    uvloop.run(run(loader, args.qdrant_collection_name))


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
            # use_multithreading=True,
            # max_concurrency=2,
        )
    else:
        raise Exception("Could not build loader from args")


async def run(loader: BaseLoader, collection_name: str):
    print("Setting up embeddings ...")
    embeddings = FastEmbedEmbeddings(
        cache_dir=None,
        threads=None,
        model_name="BAAI/bge-small-en-v1.5",
        _model=None,
        max_length= 512,
        doc_embed_type= "default",
        batch_size= 256,
        parallel=None,
    )

    # Dataset loader
    print("Setting up loader ...")

    print("Initializing qdrant client ...")
    client = QdrantClient()
    aclient = AsyncQdrantClient()

    print("Creating qdrant collection ...")
    await aclient.recreate_collection(
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

    futures = []
    batch_count = 1
    async for batch in abatch_iterate(iterable=loader.alazy_load(), size=batch_size):
        futures.append(vector_store.aadd_documents(batch))
        batch_count += 1

    await asyncio.gather(*futures)

    print("Getting qdrant collection statistics ...")
    collection = client.get_collection(collection_name)

    print(f"Added vectors: {collection.vectors_count}")

if __name__ == "__main__":
        main()
