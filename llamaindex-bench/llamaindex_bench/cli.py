from argparse import ArgumentParser
from llama_index.embeddings.fastembed import FastEmbedEmbedding
import uvloop

import logging
import sys
import os

import qdrant_client
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings
from llama_index.core.ingestion import IngestionPipeline
from llama_index.readers.huggingface_fs import HuggingFaceFSReader

parser = ArgumentParser(
    prog="Langchain Benchmark",
)
parser.add_argument("-d", "--dataset", required=True, help="Hugging face dataset name")
parser.add_argument("-c", "--column-name", required=True, help="Dataset column to load")
parser.add_argument(
    "-q", "--qdrant-collection-name", required=True, help="Qdrant collection name"
)


def main():
    args = parser.parse_args()
    print("Starting benchmark...")
    uvloop.run(run(args.dataset_name, args.column_name, args.collection_name))


async def run(dataset_name: str, column_name: str, collection_name: str):
    embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # load documents
    # lol this loader is a joke
    # => TODO: Load dataset with huggingface library and see if we can lazy load it into llamaindex instead
    loader = HuggingFaceFSReader()

    # Should probably be grpc port 6334
    client = qdrant_client.AsyncQdrantClient(
        host="localhost", port=6333, prefer_grpc=True
    )
    vector_store = QdrantVectorStore(
        aclient=client,
        collection_name=collection_name,
    )

    pipeline = IngestionPipeline(
        transformations=[
            # split
            embed_model
        ],
        vector_store=vector_store,
    )

    # HF dataset here
    await pipeline.arun(documents=loader.load_dicts())

    collection = await client.get_collection(collection_name)
    print(f"Added vectors: {collection.vectors_count}")
