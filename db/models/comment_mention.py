from db.models.db_base import Base
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class CommentMentionModel(Base):
    __tablename__ = "comment_mentions"
    extend_existing = True
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_mentions_comment_user"),)

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    def __init__(self, comment_id, user_id):
        self.comment_id = comment_id
        self.user_id = user_id
