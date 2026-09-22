async def test_update_character_visual_prompt(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()
    resp = await client.put(
        f"/api/v1/characters/{char['id']}",
        json={"visual_prompt": "pale skin, white cloak", "name": "Hero Prime"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["visual_prompt"] == "pale skin, white cloak"
    assert data["name"] == "Hero Prime"


async def test_update_character_rejects_null_name(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()
    resp = await client.put(
        f"/api/v1/characters/{char['id']}",
        json={"name": None},
    )
    assert resp.status_code == 422
    assert "name" in resp.json()["detail"]


async def test_update_character_rejects_null_locked_traits(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()
    resp = await client.put(
        f"/api/v1/characters/{char['id']}",
        json={"locked_traits": None},
    )
    assert resp.status_code == 422
    assert "locked_traits" in resp.json()["detail"]


async def test_update_character_allows_null_biography(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero", "biography": "Original bio"},
        )
    ).json()
    resp = await client.put(
        f"/api/v1/characters/{char['id']}",
        json={"biography": None},
    )
    assert resp.status_code == 200
    assert resp.json()["biography"] is None


async def test_update_character_allows_null_visual_prompt(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero", "visual_prompt": "Original prompt"},
        )
    ).json()
    resp = await client.put(
        f"/api/v1/characters/{char['id']}",
        json={"visual_prompt": None},
    )
    assert resp.status_code == 200
    assert resp.json()["visual_prompt"] is None


async def test_update_character_not_found(client):
    resp = await client.put(
        "/api/v1/characters/00000000-0000-0000-0000-000000000099",
        json={"visual_prompt": "x"},
    )
    assert resp.status_code == 404
