use clap::Parser;
use swiftide::{
    indexing::{
        loaders::FileLoader,
        transformers::{ChunkMarkdown, Embed},
        EmbeddedField, Pipeline,
    },
    integrations::{fastembed::FastEmbed, qdrant::Qdrant},
};

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    dataset: String,
    #[arg(short, long)]
    collection_name: String,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let args = Args::parse();

    let qdrant = Qdrant::builder()
        .collection_name(&args.collection_name)
        .vector_size(384)
        .with_vector(EmbeddedField::Combined)
        .build()
        .unwrap();

    let client = qdrant.client();
    let _ = client.delete_collection(args.collection_name);

    Pipeline::from_loader(
        FileLoader::new(format!("../data/{}", args.dataset)).with_extensions(&["md"]),
    )
    // .then_chunk(ChunkMarkdown::from_chunk_range(10..2024))
    .then_in_batch(256, Embed::new(FastEmbed::try_default().unwrap()))
    .then_store_with(qdrant)
    .run()
    .await
    .unwrap();
}
