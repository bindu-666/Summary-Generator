from sentence_transformers import SentenceTransformer, util

# Load pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode sentences to get embeddings
embeddings = model.encode(["This is a test sentence", "This is a test sentence"])

# Compare sentences using cosine similarity
similarity = util.cos_sim(embeddings[0], embeddings[1])

print(similarity)