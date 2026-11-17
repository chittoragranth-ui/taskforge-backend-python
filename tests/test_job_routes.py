def _register_and_get_headers(client, email='user@example.com', password='secretpass'):
    response = client.post(
        '/api/v1/auth/register',
        json={
            'email': email,
            'password': password,
            'full_name': 'Test User',
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_create_job_api(client):
    headers = _register_and_get_headers(client)
    response = client.post(
        '/api/v1/jobs',
        headers=headers,
        json={
            'type': 'email',
            'payload': {'recipient': 'test@example.com'},
        },
    )

    assert response.status_code == 202, response.text
    data = response.json()
    assert data['message'] == 'Job created successfully'
    assert data['job']['type'] == 'email'
    assert data['job']['payload'] == {'recipient': 'test@example.com'}
    assert data['job']['status'] == 'queued'


def test_get_nonexistent_job(client):
    headers = _register_and_get_headers(client, email='missing@example.com')
    response = client.get('/api/v1/jobs/nonexistent-id', headers=headers)

    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


def test_user_me_and_stats(client):
    headers = _register_and_get_headers(client, email='stats@example.com')
    response = client.get('/api/v1/users/me', headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body['email'] == 'stats@example.com'
    assert body['full_name'] == 'Test User'

    stats_response = client.get('/api/v1/users/me/stats', headers=headers)
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats['total_jobs'] == 0
    assert stats['queued_jobs'] == 0
    assert stats['processing_jobs'] == 0
    assert stats['completed_jobs'] == 0
    assert stats['failed_jobs'] == 0

def test_register_duplicate_email(client):
    payload = {
        'email': 'dup@example.com',
        'password': 'secretpass',
        'full_name': 'Dup User',
    }
    first = client.post('/api/v1/auth/register', json=payload)
    assert first.status_code == 201

    second = client.post('/api/v1/auth/register', json=payload)
    assert second.status_code == 409
    assert second.json()['detail'] == 'Email already registered'


def test_login_invalid_credentials(client):
    client.post('/api/v1/auth/register', json={'email': 'wrong@example.com', 'password': 'secretpass', 'full_name': 'Test'})
    response = client.post('/api/v1/auth/login', json={'email': 'wrong@example.com', 'password': 'wrongpass1'})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid email or password'


def test_unauthorized_job_access(client):
    response = client.get('/api/v1/jobs')
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


def test_invalid_status_transition(client):
    headers = _register_and_get_headers(client, email='invalidstatus@example.com')
    created = client.post('/api/v1/jobs', headers=headers, json={'type':'math','payload':{'left':1,'right':2,'operation':'add'}})
    job_id = created.json()['job']['id']
    response = client.patch(f'/api/v1/jobs/{job_id}/status', headers=headers, json={'status':'failed'})
    assert response.status_code == 400
    assert 'Invalid job status transition' in response.json()['detail']
