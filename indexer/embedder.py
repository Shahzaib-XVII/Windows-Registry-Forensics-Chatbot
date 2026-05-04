import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import chromadb
from sentence_transformers import SentenceTransformer
from indexer.db import get_connection

CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_store")
COLLECTION_NAME = "forensics_logs"

# Load the embedding model once
print("[EMBEDDER] Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("[EMBEDDER] Model loaded.")

def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def embed_events(batch_size=500):
    conn = get_connection()
    cursor = conn.cursor()

    important_event_ids = (
        '4624', '4625', '4634', '4647',
        '4688', '4689',
        '4698', '4699', '4700', '4702',
        '7034', '7035', '7036', '7040', '7045',
        '4663', '4656',
        '4720', '4722', '4724', '4728',
        '1102', '104',
        '4776', '4771',
        '6005', '6006', '6008',
        '4732', '4733',
    )

    placeholders = ",".join("?" * len(important_event_ids))
    cursor.execute(f"""
        SELECT id, event_id, timestamp, source, computer, message, level, file_source 
        FROM events 
        WHERE event_id IN ({placeholders})
    """, important_event_ids)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[EMBEDDER] No matching events found. Embedding all events instead...")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, event_id, timestamp, source, computer, message, level, file_source FROM events LIMIT 5000")
        rows = cursor.fetchall()
        conn.close()

    collection = get_chroma_collection()
    total = len(rows)
    print(f"[EMBEDDER] Embedding {total} forensic event records...")

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        texts, ids, metadatas = [], [], []

        for row in batch:
            text = (
                f"EventID {row['event_id']} "
                f"Source {row['source']} "
                f"Level {row['level']} "
                f"Computer {row['computer']} "
                f"Message {row['message']} "
                f"Time {row['timestamp']}"
            )
            texts.append(text)
            ids.append(f"event_{row['id']}")
            metadatas.append({
                "type": "event",
                "event_id": str(row['event_id']),
                "timestamp": str(row['timestamp']),
                "source": str(row['source']),
                "computer": str(row['computer']),
                "level": str(row['level']),
                "file_source": str(row['file_source']),
                "db_id": str(row['id'])
            })

        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        collection.upsert(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
        print(f"[EMBEDDER] Events: {min(i + batch_size, total)}/{total}")

    print("[EMBEDDER] All events embedded successfully.")


def embed_registry(batch_size=500):
    conn = get_connection()
    cursor = conn.cursor()

    forensic_keywords = [
        "Uninstall", "Run", "RunOnce", "USBSTOR", "RecentDocs",
        "TypedURLs", "LogonUI", "TimeZoneInformation", "Interfaces",
        "UserAssist", "MuiCache", "Shimcache", "AppCompatCache",
        "Services", "StartMenu", "Explorer",
    ]

    conditions = " OR ".join([f"key_path LIKE '%{kw}%'" for kw in forensic_keywords])
    cursor.execute(f"""
        SELECT id, hive, key_path, value_name, value_data, value_type, file_source 
        FROM registry_entries 
        WHERE {conditions}
        LIMIT 10000
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[EMBEDDER] No registry entries found.")
        return

    collection = get_chroma_collection()
    total = len(rows)
    print(f"[EMBEDDER] Embedding {total} forensic registry records...")

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        texts, ids, metadatas = [], [], []

        for row in batch:
            text = (
                f"Registry {row['hive']} "
                f"Key {row['key_path']} "
                f"Value {row['value_name']} "
                f"Data {row['value_data']}"
            )
            texts.append(text)
            ids.append(f"reg_{row['id']}")
            metadatas.append({
                "type": "registry",
                "hive": str(row['hive']),
                "key_path": str(row['key_path']),
                "value_name": str(row['value_name']),
                "value_data": str(row['value_data'][:200]),
                "file_source": str(row['file_source']),
                "db_id": str(row['id'])
            })

        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        collection.upsert(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
        print(f"[EMBEDDER] Registry: {min(i + batch_size, total)}/{total}")

    print("[EMBEDDER] All forensic registry entries embedded.")


def search(query, n_results=5):
    collection = get_chroma_collection()
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results