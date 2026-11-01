def test_create_job_api(client):
    response = client.post(
        "/api/v1/jobs",
        json={
            "type": "email",
            "payload": {
                "recipient": "test@example.com"
            }
        }
    )

    assert response.status_code == 202

    data = response.json()

    assert data["job"]["type"] == "email"
    assert data["job"]["payload"] == {
        "recipient": "test@example.com"
    }
    assert data["job"]["status"] == "queued"

