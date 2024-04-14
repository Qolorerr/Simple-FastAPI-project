from sqlalchemy.orm import Mapped, mapped_column

from src.db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(nullable=False)
    token: Mapped[str] = mapped_column(nullable=False)
    admin: Mapped[bool] = mapped_column(nullable=False, default=False)
