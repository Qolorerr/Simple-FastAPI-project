from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db_session import SqlAlchemyBase


class Tag(SqlAlchemyBase):
    __tablename__ = 'tags'
    __table_args__ = {'extend_existing': True}
    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)


class Banner(SqlAlchemyBase):
    __tablename__ = 'banners'
    __table_args__ = {'extend_existing': True}
    banner_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feature_id: Mapped[int] = mapped_column(nullable=False)
    tags: Mapped[list[Tag]] = relationship(secondary='banner_tags', lazy="selectin")
    content:  Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(nullable=False)
    updated_at: Mapped[str] = mapped_column(nullable=False)

    def get_as_dict(self) -> dict[str, int | str | bool | list[int]]:
        return {
            "banner_id": self.banner_id,
            "tag_ids": [tag.tag_id for tag in self.tags],
            "feature_id": self.feature_id,
            "content": self.content,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class BannerTag(SqlAlchemyBase):
    __tablename__ = 'banner_tags'
    __table_args__ = {'extend_existing': True}
    banner_tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    banner_id: Mapped[int] = mapped_column(ForeignKey("banners.banner_id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.tag_id"), nullable=False)
