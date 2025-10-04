import time
from pinecone import Pinecone, ServerlessSpec
from datetime import datetime
from dotenv import load_dotenv
from typing import List
from uuid import uuid4
import os
import json

CATALOG_FILE = "jokes_catalog.json"


load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")


def get_pinecone_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    spec = ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)

    existing_indexes = {i["name"]: i for i in pc.list_indexes()}
    matching_indexes = [name for name in existing_indexes if name.startswith(PINECONE_INDEX_NAME)]

    if matching_indexes:
        index_name = matching_indexes[0]
        print(f" Using existing Pinecone index: {index_name}")

    else:
        print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")

        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=1024,
            metric="cosine",
            spec=spec
        )
        while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
            time.sleep(1)

        index_name = PINECONE_INDEX_NAME
        print(f"Created Pinecone index: {index_name}")

    pinecone_index = pc.Index(index_name)

    return pinecone_index


def save_jokes_to_pinecone(text: str, category: str, embedding: List[float]):
    index = get_pinecone_index()
    joke_id = str(uuid4())   # unique ID
    timestamp = datetime.now().isoformat()

    # Save to Pinecone
    index.upsert([
        (
            joke_id,
            embedding,
            {
                "text": text,
                "category": category,
                "timestamp": timestamp
            }
        )
    ])

    # Save ID + metadata to JSON catalog
    catalog_entry = {
        "id": joke_id,
        "text": text,
        "category": category,
        "timestamp": timestamp
    }

    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = []

    catalog.append(catalog_entry)

    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"Joke saved (ID: {joke_id})")


def is_duplicate_joke(embedding: List[float], threshold: float = 0.85) -> bool:
    index = get_pinecone_index()
    results = index.query(vector=embedding, top_k=1, include_metadata=True)

    if results.matches:
        best = results.matches[0]
        if best.score >= threshold:
            print(f" Duplicate joke found: {best.metadata['text']}")
            return True
        return False
