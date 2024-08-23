import itertools

from fasthtml import common as fh
from qdrant_client import models

PICO_COLORS = (
    "red",
    "pink",
    "fuchsia",
    "purple",
    "violet",
    "indigo",
    "blue",
    "azure",
    "cyan",
    "jade",
    "green",
    "lime",
    "yellow",
    "amber",
    "pumpkin",
    "orange",
    "sand",
    "grey",
    "zinc",
    "slate",
)


def alternative_names(point: models.ScoredPoint):
    """Format the alternative names of the plant"""
    names = itertools.chain(
        point.payload.get("scientific_name") or [],
        point.payload.get("other_name") or [],
    )
    if not names:
        return []
    return [
        fh.H6("Alternative names"),
        fh.P(" / ".join(names)),
    ]


def region_badges(point: models.ScoredPoint):
    """Format the regions as badges"""
    regions = point.payload.get("origin") or []
    return [
        fh.Mark(
            region,
            cls=f"pico-background-{PICO_COLORS[hash(region) % len(PICO_COLORS)]}-600",
        )
        for region in regions
    ]


def search_result(point: models.ScoredPoint):
    """Format a single search result to be displayed"""
    default_image = point.payload.get("default_image") or {}
    thumbnail_url = default_image.get("thumbnail")
    # Use placeholder if thumbnail is not available
    if not thumbnail_url:
        thumbnail_url = "https://via.placeholder.com/200"

    return fh.Article(
        # Title with the common name of the plant
        fh.H3(point.payload["common_name"]),
        # Image of the plant with some additional information
        fh.Div(
            # Default image of the plant
            fh.Img(
                src=thumbnail_url,
                alt=point.payload["common_name"],
                cls="thumbnail",
            ),
            fh.Div(
                # All the regions where the plant can be found
                *region_badges(point),
                cls="badges",
            ),
            cls="grid thumbnail-container",
        ),
        # Similarity score of the result
        fh.P(fh.B("Similarity score")),
        fh.Progress(value=point.score, max=1.0, data_tooltip=point.score),
        # Description of the plant
        fh.P(point.payload["description"]),
        # All the different names of the plant
        *alternative_names(point),
    )
