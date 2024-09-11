use std::path::PathBuf;

use clap::{Parser, Subcommand, ValueEnum};
use swiftide::{
    indexing::{
        loaders::FileLoader,
        transformers::{ChunkMarkdown, Embed},
        EmbeddedField, Pipeline,
    },
    integrations::{fastembed::FastEmbed, parquet::Parquet, qdrant::Qdrant},
    traits::Loader,
};

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    collection_name: String,

    #[command(subcommand)]
    loader: LoaderArgs,
}

#[derive(Subcommand)]
enum LoaderArgs {
    /// Load from raw file
    Filename { filename: String },
    /// Load from parquet file and columns
    Parquet { path: PathBuf, column: String },
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let args = Args::parse();

    let batch_size = 256;
    let qdrant = Qdrant::builder()
        .collection_name(&args.collection_name)
        .vector_size(384)
        .with_vector(EmbeddedField::Combined)
        .batch_size(24)
        .build()
        .unwrap();

    let client = qdrant.client();
    let _ = client.delete_collection(args.collection_name);

    let loader = build_loader(&args.loader);

    Pipeline::from_loader(loader)
        // .then_chunk(ChunkMarkdown::from_chunk_range(10..2024))
        .then_in_batch(
            batch_size,
            Embed::new(
                FastEmbed::try_default()
                    .unwrap()
                    .with_batch_size(batch_size)
                    .to_owned(),
            ),
        )
        .then_store_with(qdrant)
        .run()
        .await
        .unwrap();
}

fn build_loader(args: &LoaderArgs) -> Box<dyn Loader> {
    match args {
        LoaderArgs::Filename { filename } => {
            Box::new(FileLoader::new(format!("../data/{}", filename)).with_extensions(&["md"]))
        }
        LoaderArgs::Parquet { path, column } => Box::new(
            Parquet::builder()
                .path(path)
                .column_name(column)
                .build()
                .unwrap(),
        ),
    }
}
