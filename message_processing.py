import spacy

# Load SpaCy English model
nlp = spacy.load("en_core_web_lg")

def preprocess_message(message):
    """
    Preprocess a message by tokenizing and removing stop words.
    """
    doc = nlp(message)
    tokens = [token for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(token.text for token in tokens)

def embed_message(message):
    """
    Embed a preprocessed message using the SpaCy model.
    """
    doc = nlp(message)
    return doc.vector
