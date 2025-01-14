from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import requests
import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import tempfile

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['PROCESSOR_URL'] = os.getenv('PROCESSOR_URL', 'http://document-processor:5001')
app.config['SEARCH_URL'] = os.getenv('SEARCH_URL', 'http://search:5002')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/documents/process', methods=['POST'])
def process_documents():
    """
    Process uploaded documents:
    1. Save uploaded files
    2. Send to document processor
    3. Index processed documents in search service
    """
    if 'documents' not in request.files:
        return jsonify({'error': 'No documents provided'}), 400

    files = request.files.getlist('documents')
    processed_docs = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                # Save file temporarily
                file.save(filepath)

                # Send to document processor
                with open(filepath, 'rb') as f:
                    processor_response = requests.post(
                        f"{app.config['PROCESSOR_URL']}/process",
                        files={'document': f}
                    )
                processor_response.raise_for_status()

                processed_doc = processor_response.json()
                processed_docs.append(processed_doc)

                # Clean up temporary file
                os.remove(filepath)

            except Exception as e:
                logger.error(f"Error processing document {filename}: {str(e)}")
                return jsonify({
                    'error': f'Error processing document {filename}',
                    'details': str(e)
                }), 500

    # Index processed documents
    try:
        search_response = requests.post(
            f"{app.config['SEARCH_URL']}/index",
            json={'documents': processed_docs}
        )
        search_response.raise_for_status()
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        return jsonify({
            'error': 'Error indexing documents',
            'details': str(e)
        }), 500

    return jsonify({
        'status': 'success',
        'processed_documents': len(processed_docs),
        'documents': processed_docs
    })

@app.route('/api/search', methods=['GET'])
def search_documents():
    """
    Search documents with optional cluster filtering
    """
    query = request.args.get('query', '')
    cluster_id = request.args.get('cluster_id')

    try:
        search_params = {'query': query}
        if cluster_id:
            search_params['cluster_id'] = cluster_id

        response = requests.get(
            f"{app.config['SEARCH_URL']}/search",
            params=search_params
        )
        response.raise_for_status()

        return jsonify(response.json())

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            'error': 'Search failed',
            'details': str(e)
        }), 500

@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """
    Get document clusters information
    """
    try:
        response = requests.get(f"{app.config['PROCESSOR_URL']}/clusters")
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error getting clusters: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve clusters',
            'details': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Check health of all services
    """
    health_status = {
        'api': 'healthy',
        'document_processor': 'unknown',
        'search': 'unknown'
    }

    # Check document processor
    try:
        processor_response = requests.get(f"{app.config['PROCESSOR_URL']}/health")
        processor_response.raise_for_status()
        health_status['document_processor'] = 'healthy'
    except Exception as e:
        health_status['document_processor'] = f'unhealthy: {str(e)}'

    # Check search service
    try:
        search_response = requests.get(f"{app.config['SEARCH_URL']}/status")
        search_response.raise_for_status()
        health_status['search'] = 'healthy'
    except Exception as e:
        health_status['search'] = f'unhealthy: {str(e)}'

    return jsonify(health_status)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
