from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import redis
import json
import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor
from elasticsearch.exceptions import ConnectionError

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize connections with retry logic
def init_elasticsearch(max_retries=5, delay=5):
    """Initialize Elasticsearch connection with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Elasticsearch (attempt {attempt + 1}/{max_retries})")
            es = Elasticsearch(['http://elasticsearch:9200'])
            # Test the connection
            es.info()
            logger.info("Successfully connected to Elasticsearch")
            return es
        except ConnectionError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to Elasticsearch after {max_retries} attempts")
                raise
            logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {delay} seconds...")
            time.sleep(delay)

def init_redis(max_retries=5, delay=5):
    """Initialize Redis connection with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Redis (attempt {attempt + 1}/{max_retries})")
            redis_client = redis.Redis(host='redis', port=6379)
            redis_client.ping()  # Test the connection
            logger.info("Successfully connected to Redis")
            return redis_client
        except redis.ConnectionError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect to Redis after {max_retries} attempts")
                raise
            logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {delay} seconds...")
            time.sleep(delay)

# Initialize connections
try:
    es = init_elasticsearch()
    redis_client = init_redis()
except Exception as e:
    logger.error(f"Fatal error during initialization: {str(e)}")
    raise

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
        raise

# Rest of the code remains the same...
# (Previous route handlers and functions)

if __name__ == '__main__':
    # Wait for services to be ready
    time.sleep(10)  # Give Elasticsearch and Redis time to start
    create_index()
    app.run(host='0.0.0.0', port=5002)
