from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.document_loaders import TextLoader

from multiprocessing import cpu_count

from argparse import ArgumentParser
import uvloop

parser = ArgumentParser(
    prog="Langchain Benchmark",
)
parser.add_argument("-d", "--dataset", required=True, help="Hugging face dataset name")
parser.add_argument(
    "-q", "--qdrant-collection-name", required=True, help="Qdrant collection name"
)


def main():
    args = parser.parse_args()
    print("Starting benchmark...")
    uvloop.run(run(args.dataset, args.qdrant_collection_name))


async def run(dataset_name: str, collection_name: str):
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

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    loader = DirectoryLoader(
        f"../data/{dataset_name}/",
        glob="**/*.md",
        show_progress=True,
        loader_cls=UnstructuredMarkdownLoader,
    )

    # probably: loader.alazy_load()
    #
    documents = sum(
        map(
            text_splitter.split_text,
            map(lambda d: d.page_content, loader.lazy_load()),
        ),
        [],
    )

    print(f"Embedding {len(documents)} chunks ...")

    # Qdrant
    # Can this even be async?
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
    await vector_store.aadd_documents(documents)

    print("Getting qdrant collection statistics ...")
    collection = client.get_collection(collection_name)

    print(f"Added vectors: {collection.vectors_count}")
