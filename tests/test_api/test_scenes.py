async def test_create_scene(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    response = await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={
        "scene_number": 1,
        "title": "Opening",
        "location": "Forest"
    })
    assert response.status_code == 200
    assert response.json()["scene_number"] == 1


async def test_create_shot(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    scene = (await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={"scene_number": 1})).json()
    response = await client.post(f"/api/v1/scenes/{scene['id']}/shots", json={
        "shot_number": 1,
        "prompt_text": "A warrior stands in the rain"
    })
    assert response.status_code == 200
    assert response.json()["prompt_text"] == "A warrior stands in the rain"
    assert response.json()["status"] == "PENDING"
