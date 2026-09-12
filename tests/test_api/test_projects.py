

async def test_create_project(client):
    response = await client.post("/api/v1/projects", json={"title": "Test Film"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Film"
    assert data["fps"] == 24
    assert "id" in data


async def test_list_projects(client):
    await client.post("/api/v1/projects", json={"title": "Film 1"})
    await client.post("/api/v1/projects", json={"title": "Film 2"})
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) >= 2


async def test_get_project(client):
    create_resp = await client.post("/api/v1/projects", json={"title": "My Film"})
    project_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "My Film"
