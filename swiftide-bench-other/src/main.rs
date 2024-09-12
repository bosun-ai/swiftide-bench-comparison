use std::path::PathBuf;

use clap::{Parser, Subcommand, ValueEnum};
use swiftide::{
    indexing::{
        loaders::FileLoader,
        transformers::{ChunkMarkdown, Embed},
        EmbeddedField, Pipeline,
    },
    integrations::{
        fastembed::{EmbeddingModelType, FastEmbed},
        openai::OpenAI,
        parquet::Parquet,
        qdrant::Qdrant,
    },
    traits::{EmbeddingModel, Loader},
};

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    collection_name: String,

    #[arg(value_enum, short, long, default_value = "fast-embed")]
    embedding_model: EmbeddingModelArgs,

    #[arg(long, default_value = "false")]
    chunk_markdown: bool,

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

#[derive(ValueEnum, Clone, Default)]
enum EmbeddingModelArgs {
    #[default]
    FastEmbed,
    OpenAI,
}
#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let args = Args::parse();

    let batch_size = 256;
    let vector_size = match args.embedding_model {
        EmbeddingModelArgs::FastEmbed => 384,
        EmbeddingModelArgs::OpenAI => 1536,
    };

    let qdrant = Qdrant::builder()
        .collection_name(&args.collection_name)
        .vector_size(vector_size)
        .with_vector(EmbeddedField::Combined)
        .batch_size(24)
        .build()
        .unwrap();

    let client = qdrant.client();
    let _ = client.delete_collection(args.collection_name).await;

    let loader = build_loader(&args.loader);
    let embedding_model = build_embedding_model(&args.embedding_model, batch_size);

    let mut pipeline = Pipeline::from_loader(loader);

    if args.chunk_markdown {
        pipeline = pipeline.then_chunk(ChunkMarkdown::from_chunk_range(100..4096));
    }

    pipeline
        .then_in_batch(batch_size, Embed::new(embedding_model))
        .log_all()
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

fn build_embedding_model(args: &EmbeddingModelArgs, batch_size: usize) -> Box<dyn EmbeddingModel> {
    match args {
        EmbeddingModelArgs::FastEmbed => {
            Box::new(FastEmbed::builder().batch_size(batch_size).build().unwrap())
        }
        EmbeddingModelArgs::OpenAI => Box::new(
            OpenAI::builder()
                .default_embed_model("text-embedding-3-small")
                .build()
                .unwrap(),
        ),
    }
}
