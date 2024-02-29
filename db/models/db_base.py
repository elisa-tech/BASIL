from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    dt_format_str = "%Y-%m-%d %H:%M"
    dt_short_format_str = "%d %b %y %H:%M"

    STATUS_NEW = 'NEW'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_REWORK = 'REWORK'
    pass
