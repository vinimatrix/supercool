async def test_inject_context_includes_speaker_visual_reference(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    scene = (
        await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={"scene_number": 1})
    ).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero", "visual_prompt": "white cloak"},
        )
    ).json()
    shot = (
        await client.post(
            f"/api/v1/scenes/{scene['id']}/shots",
            json={
                "shot_number": 1,
                "prompt_text": "Hero enters the rain",
                "speaker_character_id": char["id"],
            },
        )
    ).json()

    resp = await client.post(f"/api/v1/shots/{shot['id']}/inject-context", json={})

    assert resp.status_code == 200
    body = resp.json()
    assert "VISUAL REFERENCE — Hero: white cloak" in body["injected_prompt"]


async def test_inject_context_without_speaker_has_no_visual_reference(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    scene = (
        await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={"scene_number": 1})
    ).json()
    shot = (
        await client.post(
            f"/api/v1/scenes/{scene['id']}/shots",
            json={"shot_number": 1, "prompt_text": "Empty hallway"},
        )
    ).json()

    resp = await client.post(f"/api/v1/shots/{shot['id']}/inject-context", json={})

    assert resp.status_code == 200
    assert "VISUAL REFERENCE" not in resp.json()["injected_prompt"]
