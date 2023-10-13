from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    dt_format_str = "%Y-%m-%d %H:%M"
    dt_short_format_str = "%d %b %y %H:%M"
    pass