import pytest
from unittest.mock import AsyncMock, MagicMock, patch


async def test_full_flow(client):
    # Create project
    proj = (await client.post("/api/v1/projects", json={"title": "Boruto TBV"})).json()

    # Create character
    char = (await client.post(f"/api/v1/projects/{proj['id']}/characters", json={
        "name": "Boruto Uzumaki",
        "locked_traits": ["fine vertical scar", "black cape"]
    })).json()

    # Create scene
    scene = (await client.post(f"/api/v1/projects/{proj['id']}/scenes", json={
        "scene_number": 1,
        "title": "The Village Gate",
        "location": "Konoha"
    })).json()

    # Create shot
    shot = (await client.post(f"/api/v1/scenes/{scene['id']}/shots", json={
        "shot_number": 1,
        "prompt_text": "Boruto dash forward and strike",
        "speaker_character_id": char["id"]
    })).json()

    # Mock NLE pipeline, start render
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"status": "ok"}

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        job = (await client.post(f"/api/v1/shots/{shot['id']}/render")).json()

    # Check job status
    status = (await client.get(f"/api/v1/jobs/{job['id']}")).json()
    assert status["status"] == "QUEUED"
