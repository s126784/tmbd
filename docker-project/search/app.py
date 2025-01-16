from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import redis
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
es = Elasticsearch(['http://elasticsearch:9200'])
redis_client = redis.Redis(host='redis', port=6379)

def create_index():
    """Create Elasticsearch index with appropriate mappings"""
    index_name = "documents"
    try:
        if not es.indices.exists(index=index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "title": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "cluster_id": {
                            "type": "integer"
                        },
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 2
                        }
                    }
                }
            }
            es.indices.create(index=index_name, body=mapping)
            logger.info(f"Created index '{index_name}'")
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")

def index_document(doc):
    """Index a single document in Elasticsearch"""
    try:
        document = {
            'content': doc.get('text_preview', ''),
            'title': doc.get('filename', ''),
            'embedding': doc.get('embedding', []),
            'stats': doc.get('stats', {}),
            'job_id': doc.get('job_id')
        }

        es.index(
            index="documents",
            document=document,
            id=doc.get('job_id')
        )
        logger.info(f"Successfully indexed document: {document['title']}")
        return True
    except Exception as e:
        logger.error(f"Error indexing document: {str(e)}")
        return False

@app.route('/index', methods=['POST'])
def index_documents():
    """Endpoint to index multiple documents"""
    if not request.is_json:
        logger.error("Request is not JSON")
        return jsonify({'error': 'Request must be JSON'}), 400

    documents = request.json.get('documents', [])
    if not documents:
        logger.error("No documents provided")
        return jsonify({'error': 'No documents provided'}), 400

    try:
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(index_document, documents))

        success_count = sum(1 for r in results if r)
        failed_count = len(documents) - success_count

        logger.info(f"Indexed {success_count} documents, {failed_count} failed")

        return jsonify({
            'status': 'success',
            'indexed_count': success_count,
            'failed_count': failed_count,
            'total_documents': len(documents)
        })
    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        return jsonify({
            'error': 'Error indexing documents',
            'details': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        es_health = es.cluster.health()
        redis_health = redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'elasticsearch': es_health,
            'redis': redis_health
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

def wait_for_services():
    """Wait for required services to be available"""
    retries = 30
    delay = 2

    # Wait for Elasticsearch
    for i in range(retries):
        try:
            es.cluster.health(wait_for_status='yellow', timeout='5s')
            logger.info("Elasticsearch is ready")
            break
        except Exception as e:
            if i == retries - 1:
                raise
            logger.warning(f"Waiting for Elasticsearch... ({i+1}/{retries})")
            time.sleep(delay)

    # Wait for Redis
    for i in range(retries):
        try:
            redis_client.ping()
            logger.info("Redis is ready")
            break
        except Exception as e:
            if i == retries - 1:
                raise
            logger.warning(f"Waiting for Redis... ({i+1}/{retries})")
            time.sleep(delay)

if __name__ == '__main__':
    wait_for_services()
    create_index()
    app.run(host='0.0.0.0', port=5002)
