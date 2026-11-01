from app.services.job_service import create_job


def test_create_job(db_session):
    job = create_job(
        db_session,
        "email",
        {"recipient": "test@example.com"}
    )

    assert job.id is not None
    assert job.type == "email"
    assert job.payload == {"recipient": "test@example.com"}
    assert job.status == "queued"
    