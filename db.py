import os
import sqlite3
import time
from annoy import AnnoyIndex
import spacy

from message_processing import preprocess_message, embed_message

# Load SpaCy English model
nlp = spacy.load("en_core_web_lg")

# Set up the SQLite database
conn = sqlite3.connect('message_history.db')
cursor = conn.cursor()

# Create tables for message history and vectors if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS message_history
                  (message_id INTEGER PRIMARY KEY, channel_id INTEGER, role TEXT, content TEXT, timestamp REAL)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS message_vectors
                  (message_id INTEGER PRIMARY KEY, channel_id INTEGER, vector BLOB, timestamp REAL)''')
conn.commit()

# Set up the Annoy index
EMBEDDING_DIM = 300  # Dimension of the embeddings
ANNOY_INDEX_PATH = "message_vectors.ann"
annoy_index = AnnoyIndex(EMBEDDING_DIM, 'angular')
annoy_index_writable = AnnoyIndex(EMBEDDING_DIM, 'angular')
message_id_to_idx = {}

def insert_message_to_db(channel_id, role, content):
    cursor.execute("INSERT INTO message_history (channel_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                   (channel_id, role, content, time.time()))
    message_id = cursor.lastrowid
    conn.commit()

    preprocessed_message = preprocess_message(content)
    vector = embed_message(preprocessed_message)
    cursor.execute("INSERT INTO message_vectors (message_id, channel_id, vector, timestamp) VALUES (?, ?, ?, ?)",
                   (message_id, channel_id, vector.tobytes(), time.time()))
    conn.commit()

    new_annoy_index = AnnoyIndex(EMBEDDING_DIM, 'angular')
    for i in range(annoy_index.get_n_items()):
        vec = annoy_index.get_item_vector(i)
        new_annoy_index.add_item(i, vec)
    new_annoy_index.add_item(message_id, vector)
    new_annoy_index.build(10)
    new_annoy_index.save(ANNOY_INDEX_PATH)

def load_annoy_index():
    annoy_index = AnnoyIndex(EMBEDDING_DIM, 'angular')
    if os.path.exists(ANNOY_INDEX_PATH):
        annoy_index.load(ANNOY_INDEX_PATH)
    return annoy_index
