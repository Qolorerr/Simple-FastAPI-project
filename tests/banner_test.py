import logging
from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient

from main import app, PostBanner
from src import base_init, create_session, User
from tests.config import DB_PATH

base_init(DB_PATH)

logger = logging.getLogger("testing")

DEFAULT_BANNER = PostBanner(tag_ids=[1, 2, 3], feature_id=1, content='{"test_banner": "smth"}', is_active=True)
DEFAULT_USERNAME = "test_user"
DEFAULT_TOKEN = "test_token"


async def _create_test_user(username: str = DEFAULT_USERNAME, token: str = DEFAULT_TOKEN,
                            admin: bool = False) -> tuple[int, str]:
    async with create_session() as session:
        user = User(username=username, token=token, admin=admin)
        session.add(user)
        await session.flush()
        await session.commit()
    return user.user_id, token


async def _delete_test_user(user_id: int) -> None:
    async with create_session() as session:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()


@asynccontextmanager
async def context_user(*args, **kwargs):
    user_id, token = await _create_test_user(*args, **kwargs)
    yield token
    await _delete_test_user(user_id)


async def _create_banners(post_banners: list[PostBanner], admin_token: str) -> list[int]:
    banner_ids = []
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for post_banner in post_banners:
            response = await ac.post(
                "/banner",
                json={
                    "feature_id": post_banner.feature_id,
                    "tag_ids": post_banner.tag_ids,
                    "content": post_banner.content,
                    "is_active": post_banner.is_active,
                },
                headers={"token": admin_token},
            )
            assert response.status_code == 201
            banner_id = response.json()["banner_id"]
            banner_ids.append(banner_id)
    return banner_ids


async def _delete_banners(banner_ids: list[int], admin_token: str) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for banner_id in banner_ids:
            response = await ac.delete(
                f"/banner/{banner_id}",
                headers={"token": admin_token},
            )
            assert response.status_code == 204


@asynccontextmanager
async def context_banners(post_banners: list[PostBanner], admin_token: str):
    banner_ids = await _create_banners(post_banners, admin_token)
    yield banner_ids
    await _delete_banners(banner_ids, admin_token)


@pytest.mark.parametrize(
    "post_banner, token, status_code",
    [
        (DEFAULT_BANNER, DEFAULT_TOKEN, 201),
        (DEFAULT_BANNER, None, 401),
        (DEFAULT_BANNER, "wrong_token", 401),
    ]
)
async def test_banner_creation(post_banner: PostBanner, token: str | None, status_code: int) -> None:
    async with context_user(admin=True) as admin_token:
        # Create new banner
        headers = {"token": token} if token else {}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/banner",
                json={
                    "feature_id": post_banner.feature_id,
                    "tag_ids": post_banner.tag_ids,
                    "content": post_banner.content,
                    "is_active": post_banner.is_active,
                },
                headers=headers,
            )
        assert response.status_code == status_code
        if status_code == 201:
            banner_id = response.json()["banner_id"]

            # Delete banner
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete(
                    f"/banner/{banner_id}",
                    headers={"token": admin_token},
                )
            assert response.status_code == 204


@pytest.mark.parametrize(
    "post_banner, token, status_code",
    [
        (DEFAULT_BANNER, DEFAULT_TOKEN, 204),
        (DEFAULT_BANNER, None, 401),
        (DEFAULT_BANNER, "wrong_token", 401),
    ]
)
async def test_banner_deletion(post_banner: PostBanner, token: str | None, status_code: int) -> None:
    async with context_user(admin=True) as admin_token:
        # Create new banner
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/banner",
                json={
                    "feature_id": post_banner.feature_id,
                    "tag_ids": post_banner.tag_ids,
                    "content": post_banner.content,
                    "is_active": post_banner.is_active,
                },
                headers={"token": admin_token},
            )
        assert response.status_code == 201
        banner_id = response.json()["banner_id"]

        # Delete banner
        headers = {"token": token} if token else {}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(
                f"/banner/{banner_id}",
                headers=headers,
            )
        assert response.status_code == status_code

        if status_code != 204:
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.delete(
                    f"/banner/{banner_id}",
                    headers={"token": admin_token},
                )


@pytest.mark.parametrize(
    "post_banners, token, params, status_code, result_banners",
    [
        ([DEFAULT_BANNER], DEFAULT_TOKEN, {"feature_id": 1, "tag_id": 1}, 200, [DEFAULT_BANNER]),
        ([DEFAULT_BANNER], None, {"feature_id": 1, "tag_id": 1}, 401, None),
        ([DEFAULT_BANNER], "wrong_token", {"feature_id": 1, "tag_id": 1}, 401, None),
    ]
)
async def test_get_banners(post_banners: list[PostBanner], token: str | None, params: dict[str, int],
                           status_code: int, result_banners: list[PostBanner]) -> None:
    async with (context_user(admin=True) as admin_token,
                context_banners(post_banners, admin_token)):
        headers = {"token": token} if token else {}
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/banner",
                params=params,
                headers=headers,
            )
        assert response.status_code == status_code
        if status_code == 200:
            result_banners = set(map(lambda x: (x.feature_id, tuple(x.tag_ids), x.content, x.is_active), result_banners))
            response_banners = response.json()
            response_banners = set(map(lambda x: (x["feature_id"], tuple(x["tag_ids"]), x["content"], x["is_active"]),
                                       response_banners))
            assert result_banners == response_banners


@pytest.mark.parametrize(
    "post_banner, feature_id, tag_id, status_code",
    [
        (DEFAULT_BANNER, 1, 1, 200),
        (DEFAULT_BANNER, 1, 4, 404),
        (DEFAULT_BANNER, 2, 1, 404),
    ]
)
async def test_user_banner(post_banner: PostBanner, feature_id: int, tag_id: int, status_code: int) -> None:
    async with (context_user() as user_token,
                context_user(token="admin_token", admin=True) as admin_token,
                context_banners([post_banner], admin_token)):
        # Get banner
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/user_banner",
                params={"feature_id": feature_id, "tag_id": tag_id},
                headers={"token": user_token},
            )
        assert response.status_code == status_code
        if status_code == 200:
            assert str(response.json()) == post_banner.content


@pytest.mark.parametrize(
    "post_banner, params, status_code",
    [
        (DEFAULT_BANNER, {"tag_ids": [2]}, 200),
        (DEFAULT_BANNER, {"feature_id": 2}, 200),
        (DEFAULT_BANNER, {"content": "smth_2"}, 200),
        (DEFAULT_BANNER, {"is_active": False}, 200),
    ]
)
async def test_patch_banner(post_banner: PostBanner, params: dict[str, int | str | bool | list[int]],
                            status_code: int):
    async with (context_user(admin=True) as admin_token,
                context_banners([post_banner], admin_token) as banner_ids):
        banner_id = banner_ids[0]
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.patch(
                f"/banner/{banner_id}",
                json=params,
                headers={"token": admin_token},
            )
        assert response.status_code == status_code
        if status_code != 200:
            return
        get_params = {
            "feature_id": params["feature_id"] if "feature_id" in params else post_banner.feature_id,
            "tag_ids": params["tag_ids"] if "tag_ids" in params else post_banner.tag_ids[0],
            "limit": 1,
        }
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/banner",
                params=get_params,
                headers={"token": admin_token},
            )
        assert response.status_code == 200
        assert len(response.json()) == 1
        banner = response.json()[0]
        if "tag_ids" in params:
            assert banner["tag_ids"] == params["tag_ids"]
        if "feature_id" in params:
            assert banner["feature_id"] == params["feature_id"]
        if "content" in params:
            assert banner["content"] == params["content"]
        if "is_active" in params:
            assert banner["is_active"] == params["is_active"]
