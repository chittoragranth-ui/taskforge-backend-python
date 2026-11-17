from app.models import User
from app.services.job_service import create_job


def test_create_job(db_session):
    user = User(email='user@example.com', hashed_password='x', full_name='User Example')
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    job = create_job(
        db_session,
        'email',
        {'recipient': 'test@example.com'},
        user_id=user.id,
    )

    assert job.id is not None
    assert job.type == 'email'
    assert job.payload == {'recipient': 'test@example.com'}
    assert job.status == 'queued'
    assert job.user_id == user.id
