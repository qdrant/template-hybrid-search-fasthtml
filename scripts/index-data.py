import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models

main_directory = Path(__file__).parent.parent

# Load the environment variables from the .env file in the parent directory
load_dotenv(dotenv_path=main_directory / ".env")

# Load both sparse and dense models
dense_model = TextEmbedding("Qdrant/clip-ViT-B-32-text")
sparse_model = SparseTextEmbedding("Qdrant/bm25")

# Load the dataset with the different plant species
with open(main_directory / "data" / "species-detailed.jsonl") as f:
    all_species = [json.loads(line) for line in f]

# Connect to Qdrant server
client = QdrantClient(
    location=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)


def format_species(species: dict) -> str:
    """
    Format species to be used as a document to index. It mixes multiple attributes to create a single text
    description of the species.
    :param species:
    :return:
    """
    description = species["description"]
    if len(species["other_name"]) > 0:
        description += "\n\nOther names: " + ", ".join(species["other_name"])
    return description


# Format the texts and get the embeddings
texts = list(map(format_species, all_species))
dense_embeddings = dense_model.passage_embed(texts)
sparse_embeddings = sparse_model.passage_embed(texts)

# Create a Qdrant collection and index the documents
client.create_collection(
    collection_name=os.environ["COLLECTION_NAME"],
    vectors_config={
        "clip-ViT-B-32-text": models.VectorParams(
            size=512,  # Size of the clip-ViT-B-32 embeddings
            distance=models.Distance.COSINE,
        ),
    },
    sparse_vectors_config={
        "bm25": models.SparseVectorParams(
            modifier=models.Modifier.IDF,  # Use the IDF modifier to calculate the BM25 score
        ),
    },
)

# Finally index the documents with the embeddings
client.upload_points(
    collection_name=os.environ["COLLECTION_NAME"],
    points=[
        models.PointStruct(
            id=uuid.uuid4().hex,
            vector={
                "clip-ViT-B-32-text": dense_embedding.tolist(),
                "bm25": sparse_embedding.as_object(),
            },
            payload=doc,
        )
        for doc, dense_embedding, sparse_embedding in zip(
            all_species, dense_embeddings, sparse_embeddings
        )
    ],
)
