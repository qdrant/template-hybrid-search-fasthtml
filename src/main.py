import os
from pathlib import Path

from dotenv import load_dotenv
from fastembed import SparseTextEmbedding, TextEmbedding
from fasthtml import common as fh
from qdrant_client import QdrantClient, models

from components import search_result

main_directory = Path(__file__).parent.parent

# Load the environment variables from the .env file in the parent directory
load_dotenv(dotenv_path=main_directory / ".env")

# Load both sparse and dense models
dense_model = TextEmbedding("Qdrant/clip-ViT-B-32-text")
sparse_model = SparseTextEmbedding("Qdrant/bm25")

# Connect to Qdrant server
client = QdrantClient(
    location=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

# Create a FastHTML app
app, route = fh.fast_app(
    pico=True,  # Load Pico CSS micro-framework
    htmlkw={"data-theme": "light"},  # Set the default theme to light
    hdrs=(
        fh.Link(
            href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css",
            rel="stylesheet",
        ),  # Load Pico CSS colors
        fh.Link(href="assets/custom-styles.css", rel="stylesheet"),  # Load custom CSS
    ),
)


@route("/")
def get():
    """Main page with search functionality"""
    return (
        # Return title first, so it's displayed in the browser tab
        fh.Title("Plant species search"),
        fh.Header(
            # Title of the current page
            fh.H1("Plant species search"),
            # Search form
            fh.P(
                "This simple app lets you find the care guides for a plant. "
                "It uses two models to index the data: clip-ViT-B-32-text for dense embeddings and Qdrant/bm25. "
                "The intermediate search results are combined using Reciprocal Rank Fusion (RRF). "
                "Enter a search query to find more information about a plant you're interested in.",
            ),
            fh.Form(
                fh.Group(
                    fh.Input(type="search", id="query"),
                    fh.Button("Search"),
                ),
                enctype="application/json",
                hx_post="/search",
                hx_target="#search-results",
            ),
            cls="container",
        ),
        # Container for the search results
        fh.Main(
            fh.H2("Search results"),
            fh.Div(
                fh.P("Please enter a search query to see the results."),
                id="search-results",
            ),
            cls="container",
        ),
    )


@route("/search")
def post(query: str):
    """Search endpoint providing search results for given query"""
    # Create both dense and sparse embeddings for the query
    dense_query = dense_model.query_embed(query)
    sparse_query = sparse_model.query_embed(query)

    # Search the Qdrant collection with the query embeddings and use RRF to combine the results
    results = client.query_points(
        collection_name=os.environ["COLLECTION_NAME"],
        prefetch=[
            models.Prefetch(
                query=next(dense_query).tolist(),
                using="clip-ViT-B-32-text",
                limit=12,
            ),
            models.Prefetch(
                query=next(sparse_query).as_object(),
                using="bm25",
                limit=12,
            ),
        ],
        query=models.FusionQuery(
            fusion=models.Fusion.RRF,  # Reciprocal Rank Fusion combines the results
        ),
        limit=9,
    )

    # Create all the containers for each individual search result
    containers = [search_result(result) for result in results.points]

    # Display the results in a grid
    return fh.Section(
        *containers,
        cls="examples-list",
    )


if __name__ == "__main__":
    # Start the FastHTML app
    fh.serve()
