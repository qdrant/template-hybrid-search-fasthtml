import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

main_directory = Path(__file__).parent.parent

# Load the environment variables from the .env file in the parent directory
load_dotenv(dotenv_path=main_directory / ".env")

# Set up the API key and base URL
BASE_URL = "https://perenual.com/api"
API_KEY = os.environ["PERENUAL_API_KEY"]

# Iterate over all the pages and collect the species data
species = []
with requests.Session() as s:
    page, max_pages = 1, 1
    while page <= max_pages:  # 30 species per page
        response = s.get(
            f"{BASE_URL}/species-list", params={"key": API_KEY, "page": page}
        )
        response_json = response.json()
        species.extend(response_json.get("data", []))
        max_pages = response_json.get("last_page", 1)
        with open(main_directory / "data" / "species.json", "w") as f:
            json.dump(species, f, indent=4)

        # Load the next page
        page += 1

    # Get the details of each species and save them in a JSONL file
    with open(main_directory / "data" / "species.json") as f:
        species = json.load(f)

    # Iterate over each species and get the details
    for current_species in tqdm(species):
        species_id = current_species["id"]
        response = s.get(
            f"{BASE_URL}/species/details/{current_species['id']}",
            params={"key": API_KEY},
        )
        response_json = response.json()
        if response.status_code != 200:
            print(f"Failed to get details for species {species_id}")
            print(response_json)
            break

        with open(main_directory / "data" / "species-detailed.jsonl", "a+") as f:
            json.dump(response_json, f)
            f.write("\n")
