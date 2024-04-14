import logging.config
from datetime import datetime
from typing import Annotated

import uvicorn
from fastapi import FastAPI, status, Header, Path, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from starlette.responses import JSONResponse, Response

from src import Banner, User, base_init, create_session, Tag
from src.config import DB_PATH, LOGGER_CONFIG

app = FastAPI()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger("app")


async def user_token_verification(token: Annotated[str | None, Header()] = None):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    async with create_session() as session:
        query = select(User).where(User.token == token)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def admin_token_verification(token: Annotated[str | None, Header()] = None):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    async with create_session() as session:
        query = select(User).where(User.token == token)
        result = (await session.scalars(query)).all()
        if len(result) < 1:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        if not result[0].admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@app.get("/user_banner", dependencies=[Depends(user_token_verification)])
async def user_banner(tag_id: int, feature_id: int, use_last_revision: bool = True):
    async with create_session() as session:
        tag = await session.get(Tag, tag_id)
        if tag is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        query = select(Banner).join(Banner.tags).where((Banner.feature_id == feature_id) &
                                                       (Tag.tag_id == tag_id) &
                                                       Banner.is_active)
        results = (await session.scalars(query)).all()
        if len(results) < 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        content = results[0].content
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@app.get("/banner", dependencies=[Depends(admin_token_verification)])
async def get_banners(feature_id: int | None = None, tag_id: int | None = None,
                      limit: int | None = None, offset: int | None = 0):
    async with create_session() as session:
        if tag_id is not None:
            tag = await session.get(Tag, tag_id)
            if tag is None:
                return JSONResponse(content=[], status_code=status.HTTP_200_OK)
        query = select(Banner).join(Banner.tags).where(
            ((Banner.feature_id == feature_id) if feature_id is not None else True) &
            ((Tag.tag_id == tag_id) if tag_id is not None else True))
        results = (await session.scalars(query)).all()
        if limit is not None:
            results = results[offset:offset + limit]

        for i in range(len(results)):
            results[i] = results[i].get_as_dict()
        return JSONResponse(content=results, status_code=status.HTTP_200_OK)


class PostBanner(BaseModel):
    tag_ids: list[int]
    feature_id: int
    content: str
    is_active: bool = True


@app.post("/banner", dependencies=[Depends(admin_token_verification)])
async def post_banner(args: PostBanner):
    async with create_session() as session:
        banner = Banner(feature_id=args.feature_id, content=args.content,
                        is_active=args.is_active, created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat())
        for tag_id in args.tag_ids:
            tag = await session.get(Tag, tag_id)
            if tag is None:
                tag = Tag(tag_id=tag_id)
                session.add(tag)
            banner.tags.append(tag)
        session.add(banner)
        await session.flush()
        await session.commit()
        return JSONResponse(content={"banner_id": banner.banner_id}, status_code=status.HTTP_201_CREATED)


class PatchBanner(BaseModel):
    tag_ids: list[int] | None = None
    feature_id: int | None = None
    content: str | None = None
    is_active: bool | None = None


@app.patch("/banner/{banner_id}", dependencies=[Depends(admin_token_verification)])
async def patch_banner(args: PatchBanner, banner_id: Annotated[int, Path()]):
    async with create_session() as session:
        banner = await session.get(Banner, banner_id)
        if banner is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        if args.tag_ids is not None:
            banner.tags = []
            for tag_id in args.tag_ids:
                tag = await session.get(Tag, tag_id)
                if tag is None:
                    tag = Tag(tag_id=tag_id)
                    session.add(tag)
                banner.tags.append(tag)
        if args.feature_id is not None:
            banner.feature_id = args.feature_id
        if args.content is not None:
            banner.content = args.content
        if args.is_active is not None:
            banner.is_active = args.is_active
        banner.updated_at = datetime.now().isoformat()

        await session.commit()
        return Response(status_code=status.HTTP_200_OK)


@app.delete("/banner/{banner_id}", dependencies=[Depends(admin_token_verification)])
async def delete_banner(banner_id: Annotated[int, Path()]):
    async with create_session() as session:
        banner = await session.get(Banner, banner_id)
        if banner:
            await session.delete(banner)
            await session.commit()
        else:
            return status.HTTP_404_NOT_FOUND
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == '__main__':
    base_init(DB_PATH)
    uvicorn.run("main:app", port=8000, reload=False, log_level="info")
