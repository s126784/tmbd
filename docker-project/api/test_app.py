import pytest
from app import app
import io
import json
from unittest.mock import patch, Mock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint"""
    with patch('requests.get') as mock_get:
        # Mock responses from services
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: {'status': 'healthy'}),
            Mock(status_code=200, json=lambda: {'status': 'healthy'})
        ]

        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['api'] == 'healthy'

def test_process_documents(client):
    """Test document processing endpoint"""
    with patch('requests.post') as mock_post:
        # Mock successful processing and indexing
        mock_post.side_effect = [
            Mock(
                status_code=200,
                json=lambda: {'id': '1', 'status': 'processed'}
            ),
            Mock(
                status_code=200,
                json=lambda: {'status': 'success', 'indexed_count': 1}
            )
        ]

        # Create test file
        test_file = (io.BytesIO(b'Test document content'), 'test.txt')

        response = client.post(
            '/api/documents/process',
            data={'documents': test_file},
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

def test_search_documents(client):
    """Test search endpoint"""
    with patch('requests.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'results': [
                    {'id': '1', 'title': 'Test Doc', 'content': 'Test content'}
                ],
                'total': 1
            }
        )

        response = client.get('/api/search?query=test')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert len(data['results']) == 1

def test_get_clusters(client):
    """Test clusters endpoint"""
    with patch('requests.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'clusters': [
                    {'id': 1, 'size': 10, 'centroid': [0.1, 0.2]},
                    {'id': 2, 'size': 15, 'centroid': [0.3, 0.4]}
                ]
            }
        )

        response = client.get('/api/clusters')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'clusters' in data
        assert len(data['clusters']) == 2

def test_invalid_file_upload(client):
    """Test upload with invalid file type"""
    test_file = (io.BytesIO(b'Invalid file content'), 'test.exe')

    response = client.post(
        '/api/documents/process',
        data={'documents': test_file},
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
