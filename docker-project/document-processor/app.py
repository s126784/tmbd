from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import redis
import json

app = Flask(__name__)
redis_client = redis.Redis(host='redis', port=6379)
vectorizer = TfidfVectorizer(max_features=1000)

def process_document_batch(documents):
    """Map function: Process a batch of documents to extract features"""
    features = vectorizer.fit_transform(documents)
    return features.toarray()

def reduce_features(feature_lists):
    """Reduce function: Combine features from multiple batches"""
    combined_features = np.vstack(feature_lists)
    return combined_features

@app.route('/process', methods=['POST'])
def process_documents():
    documents = request.json['documents']
    batch_size = int(request.json.get('batch_size', 100))

    # Split documents into batches for parallel processing
    batches = [documents[i:i + batch_size]
               for i in range(0, len(documents), batch_size)]

    # Map phase: Process document batches in parallel
    with ProcessPoolExecutor() as executor:
        feature_lists = list(executor.map(process_document_batch, batches))

    # Reduce phase: Combine features
    combined_features = reduce_features(feature_lists)

    # Apply t-SNE for visualization
    tsne = TSNE(n_components=2, random_state=42)
    embedding = tsne.fit_transform(combined_features)

    # Store results in Redis
    result = {
        'embedding': embedding.tolist(),
        'feature_vectors': combined_features.tolist()
    }
    job_id = np.random.randint(1000000)
    redis_client.setex(f'job_{job_id}', 3600, json.dumps(result))

    return jsonify({'job_id': job_id})

@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    result = redis_client.get(f'job_{job_id}')
    if result:
        return jsonify(json.loads(result))
    return jsonify({'error': 'Results not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
