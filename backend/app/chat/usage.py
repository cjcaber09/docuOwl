"""The daily question limit."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Usage


def today_utc() -> date:
    return datetime.now(UTC).date()


def use_one_question(db: Session, user_id: uuid.UUID, limit: int, day: date | None = None) -> bool:
    """Counts one question for the day. False when the day's limit is already used up.

    One statement does both the check and the +1, so two questions sent at the same moment
    can't both slip past the limit.
    """
    statement = (
        insert(Usage)
        .values(user_id=user_id, day=day or today_utc(), questions_asked=1)
        .on_conflict_do_update(
            index_elements=[Usage.user_id, Usage.day],
            set_={"questions_asked": Usage.questions_asked + 1},
            where=Usage.questions_asked < limit,
        )
        .returning(Usage.questions_asked)
    )
    counted = db.execute(statement).scalar_one_or_none()
    db.commit()
    return counted is not None
