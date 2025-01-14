import pytest
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_status_endpoint(client):
    """Test the status endpoint"""
    response = client.get('/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] in ['healthy', 'unhealthy']

def test_search_endpoint(client):
    """Test the search endpoint"""
    # Test empty search
    response = client.get('/search?query=')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'results' in data
    assert 'total' in data

    # Test with query
    response = client.get('/search?query=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_index_endpoint(client):
    """Test document indexing"""
    test_docs = [{
        'id': '1',
        'title': 'Test Document',
        'content': 'This is a test document',
        'cluster_id': 1
    }]

    response = client.post('/index',
                         data=json.dumps({'documents': test_docs}),
                         content_type='application/json')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['indexed_count'] > 0
