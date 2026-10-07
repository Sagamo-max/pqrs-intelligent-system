from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.area import Area


def get_by_code(db: Session, code: str) -> Area | None:
    return db.scalar(
        select(Area).where(Area.code == code, Area.is_active.is_(True))
    )


def get_default(db: Session) -> Area:
    area = db.scalar(select(Area).where(Area.is_default.is_(True)))
    if area is None:
        raise RuntimeError(
            "No default area configured (is_default=True). "
            "Check that the seed migration was applied."
        )
    return area


def resolve_area(db: Session, code: str | None) -> Area:
    if not code:
        return get_default(db)

    area = get_by_code(db, code)
    if area is None or area.is_default:
        return get_default(db)

    return area