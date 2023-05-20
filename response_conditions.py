from datetime import datetime
from collections import defaultdict
import random
import spacy
from message_processing import preprocess_message, embed_message
from db import load_annoy_index

# Load SpaCy English model
nlp = spacy.load("en_core_web_lg")

# Define constants
SIMILARITY_THRESHOLD = 0.8
NUM_NEIGHBORS = 10
SENTIMENT_THRESHOLD = 0.5
time_since_last_response_threshold = 2
engagement_threshold = 2

# New weights for each factor
SENTIMENT_WEIGHT = 0.2
ENTITY_WEIGHT = 0.2
SIMILARITY_WEIGHT = 0.2
TIME_WEIGHT = 0.2
ENGAGEMENT_WEIGHT = 0.1
RANDOM_CHANCE_WEIGHT = 0.1

RESPONSE_THRESHOLD = 0.3  # Adjust this value to control overall responsiveness

user_engagement = defaultdict(int)

def should_bot_chime_in(message, author_id, channel_id):
    global last_response_time
    last_response_time = datetime.now()
    now = datetime.now()

    score = 0  # Initialize score

    # 1. Sentiment Analysis
    sentiment = nlp(message).sentiment
    if abs(sentiment) > SENTIMENT_THRESHOLD:
        score += SENTIMENT_WEIGHT

    # 2. Named Entity Recognition (NER)
    entities = nlp(message).ents
    if any(ent.label_ in {"PERSON", "ORG", "GPE"} for ent in entities):
        score += ENTITY_WEIGHT

    # 3. Vector database similarity search
    annoy_index = load_annoy_index()
    preprocessed_message = preprocess_message(message)
    message_vector = embed_message(preprocessed_message)
    similar_message_ids, distances = annoy_index.get_nns_by_vector(message_vector, NUM_NEIGHBORS, include_distances=True)
    if any(distance < SIMILARITY_THRESHOLD for distance in distances):
        score += SIMILARITY_WEIGHT

    # 4. Time Since Last Response
    time_since_last_response = (now - last_response_time).total_seconds()
    if time_since_last_response > time_since_last_response_threshold:
        score += TIME_WEIGHT

    # 5. User Engagement
    user_engagement[author_id] += 1
    if user_engagement[author_id] > engagement_threshold:
        score += ENGAGEMENT_WEIGHT

    # 6. Random Chance
    if random.random() > 0.5:  # 50% chance
        score += RANDOM_CHANCE_WEIGHT

    # Decide whether to respond based on total score
    should_respond = score > RESPONSE_THRESHOLD

    return score, should_respond
