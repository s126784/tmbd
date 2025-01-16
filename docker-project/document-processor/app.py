from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA  # Using PCA instead of t-SNE for single documents
import numpy as np
import redis
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
redis_client = redis.Redis(host='redis', port=6379)
vectorizer = TfidfVectorizer(
    max_features=1000,
    stop_words='english',
    lowercase=True
)

def extract_text_from_file(file):
    try:
        logger.info(f"Processing file: {file.filename}")
        if file.filename.lower().endswith('.txt'):
            content = file.read()
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    text = content.decode(encoding)
                    logger.info(f"Successfully decoded with {encoding}")
                    return text
                except UnicodeDecodeError:
                    continue
            logger.error("Failed to decode with all attempted encodings")
            return None
        else:
            logger.warning(f"Unsupported file type: {file.filename}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}", exc_info=True)
        return None

@app.route('/process', methods=['POST'])
def process_documents():
    logger.info("Received process request")
    try:
        if 'document' not in request.files:
            logger.error("No document in request")
            return jsonify({'error': 'No document provided'}), 400

        file = request.files['document']
        if not file:
            logger.error("Empty file received")
            return jsonify({'error': 'Empty file'}), 400

        # Extract text
        text = extract_text_from_file(file)
        if not text:
            logger.error("Could not extract text from document")
            return jsonify({'error': 'Could not extract text from document'}), 400

        logger.info(f"Extracted text length: {len(text)}")

        # Process text
        try:
            # Generate TF-IDF features
            features = vectorizer.fit_transform([text])
            feature_array = features.toarray()
            logger.info(f"Generated features shape: {feature_array.shape}")

            # Create a simple 2D embedding based on feature importance
            feature_importance = np.sum(feature_array, axis=0)
            top_indices = np.argsort(feature_importance)[-2:]  # Get indices of top 2 features
            embedding = feature_array[:, top_indices]
            logger.info("Feature-based embedding completed successfully")

            # Calculate some basic text statistics
            words = text.split()
            unique_words = len(set(words))

            # Store results
            result = {
                'embedding': embedding.tolist(),
                'feature_vectors': feature_array.tolist(),
                'text_preview': text[:1000],
                'filename': file.filename,
                'stats': {
                    'total_length': len(text),
                    'word_count': len(words),
                    'unique_words': unique_words
                }
            }

            job_id = np.random.randint(1000000)
            redis_client.setex(f'job_{job_id}', 3600, json.dumps(result))
            logger.info(f"Stored results with job_id: {job_id}")

            return jsonify({
                'job_id': job_id,
                'status': 'success',
                'filename': file.filename,
                'text_preview': text[:200],
                'stats': result['stats']
            })

        except Exception as e:
            logger.error(f"Error in text processing: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Error processing text',
                'details': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Unexpected error',
            'details': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
