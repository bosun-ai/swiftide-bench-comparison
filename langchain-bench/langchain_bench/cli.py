from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import HuggingFaceDatasetLoader
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from multiprocessing import cpu_count

from argparse import ArgumentParser
import uvloop

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
    loader = HuggingFaceDatasetLoader(dataset_name, column_name)
    # probably: loader.alazy_load()

    # Qdrant
    # Can this even be async?
    print("Initializing qdrant client ...")
    client = QdrantClient()

    print("Creating qdrant collection ...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    print("Creating langchain vector store ...")
    vector_store = QdrantVectorStore(
        client=client, collection_name=collection_name, embedding=embeddings
    )

    print("Async adding documents to vector store ...")
    await vector_store.aadd_texts(map(str, loader.lazy_load()))

    print("Getting qdrant collection statistics ...")
    collection = client.get_collection(collection_name)

    print(f"Added vectors: {collection.vectors_count}")
