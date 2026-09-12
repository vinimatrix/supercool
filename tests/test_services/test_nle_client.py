import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.nle_client import NLEClient


@pytest.fixture
def client():
    return NLEClient(base_url="http://localhost:8080")


@pytest.mark.asyncio
async def test_health_check_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = await client.health_check()
        assert result is True
        mock_http.get.assert_called_once_with("http://localhost:8080/health")


@pytest.mark.asyncio
async def test_health_check_failure(client):
    import httpx

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.get.side_effect = httpx.ConnectError("connection refused")
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = await client.health_check()
        assert result is False


@pytest.mark.asyncio
async def test_concat(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"output": "/tmp/out.mp4", "duration_s": 10.0}

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = await client.concat(["clip1.mp4", "clip2.mp4"], "/tmp/out.mp4")
        assert result == {"output": "/tmp/out.mp4", "duration_s": 10.0}
        mock_http.post.assert_called_once_with(
            "http://localhost:8080/api/v1/concat",
            json={"clips": ["clip1.mp4", "clip2.mp4"], "output": "/tmp/out.mp4"},
        )


@pytest.mark.asyncio
async def test_transcode(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"output": "/tmp/out_24fps.mp4"}

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = await client.transcode("/tmp/in.mp4", "/tmp/out_24fps.mp4", fps=24)
        assert result == {"output": "/tmp/out_24fps.mp4"}
        mock_http.post.assert_called_once_with(
            "http://localhost:8080/api/v1/transcode",
            json={"input": "/tmp/in.mp4", "output": "/tmp/out_24fps.mp4", "fps": 24},
        )


@pytest.mark.asyncio
async def test_mix_audio(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"output": "/tmp/mixed.wav"}

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = await client.mix_audio(["v1.wav", "bgm.wav"], "/tmp/mixed.wav")
        assert result == {"output": "/tmp/mixed.wav"}
        mock_http.post.assert_called_once_with(
            "http://localhost:8080/api/v1/mix_audio",
            json={"tracks": ["v1.wav", "bgm.wav"], "output": "/tmp/mixed.wav"},
        )


@pytest.mark.asyncio
async def test_pipeline(client):
    config = {"steps": [{"op": "concat"}, {"op": "transcode"}]}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"status": "ok", "output": "/tmp/final.mp4"}

    with patch("app.services.nle_client.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_http

        result = await client.pipeline(config)
        assert result == {"status": "ok", "output": "/tmp/final.mp4"}
        mock_http.post.assert_called_once_with(
            "http://localhost:8080/api/v1/pipeline", json=config
        )
