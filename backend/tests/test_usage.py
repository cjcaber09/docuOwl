from datetime import timedelta

from sqlalchemy import select

from app.chat.usage import today_utc, use_one_question
from app.models import Usage
from tests.helpers import make_user


def asked_today(db, user):
    db.expire_all()
    return db.scalar(select(Usage.questions_asked).where(Usage.user_id == user.id, Usage.day == today_utc()))


def test_first_question_of_the_day_counts(db):
    user = make_user(db)

    assert use_one_question(db, user.id, limit=100) is True
    assert asked_today(db, user) == 1


def test_questions_stop_at_the_limit(db):
    user = make_user(db)

    answers = [use_one_question(db, user.id, limit=2) for _ in range(3)]

    assert answers == [True, True, False]
    assert asked_today(db, user) == 2


def test_a_new_day_starts_from_zero(db):
    user = make_user(db)
    yesterday = today_utc() - timedelta(days=1)
    use_one_question(db, user.id, limit=1, day=yesterday)

    assert use_one_question(db, user.id, limit=1, day=yesterday) is False
    assert use_one_question(db, user.id, limit=1) is True
