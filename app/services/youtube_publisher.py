"""YouTube publisher for uploading finished 4K masters to YouTube.

Uses YouTube Data API v3 for resumable uploads, metadata binding,
and thumbnail setting. Supports simulation mode for testing.
"""

import os
import json
import mimetypes
from pathlib import Path

import httpx


YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_THUMBNAIL_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

SIMULATION_MODE = not os.environ.get("YOUTUBE_ACCESS_TOKEN")


class YouTubePublisher:
    """Publishes videos to YouTube with metadata and thumbnails."""

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or os.environ.get("YOUTUBE_ACCESS_TOKEN")
        self.simulation = not self.access_token

    def publish(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        category_id: str = "1",
        privacy_status: str = "unlisted",
        thumbnail_path: str | None = None,
    ) -> dict:
        """Upload a video to YouTube.

        Args:
            video_path: Path to the MP4 file.
            title: Video title.
            description: Video description.
            tags: List of tags.
            category_id: YouTube category (1 = Film & Animation).
            privacy_status: unlisted, public, or private.
            thumbnail_path: Optional path to thumbnail JPG.

        Returns:
            dict with video_id, url, and status.
        """
        if self.simulation:
            return self._simulate_upload(video_path, title)

        return self._real_upload(
            video_path, title, description, tags or [],
            category_id, privacy_status, thumbnail_path
        )

    def _simulate_upload(self, video_path: str, title: str) -> dict:
        """Simulate upload for testing without API credentials."""
        fake_id = "sim_" + Path(video_path).stem
        print(f"[SIMULATION] Would upload: {video_path}")
        print(f"[SIMULATION] Title: {title}")
        print(f"[SIMULATION] URL: https://youtu.be/{fake_id}")
        return {
            "video_id": fake_id,
            "url": f"https://youtu.be/{fake_id}",
            "status": "simulated",
            "title": title,
        }

    def _real_upload(
        self, video_path: str, title: str, description: str,
        tags: list[str], category_id: str, privacy_status: str,
        thumbnail_path: str | None
    ) -> dict:
        """Perform real resumable upload to YouTube."""
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        file_size = os.path.getsize(video_path)
        mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"

        with httpx.Client(timeout=300) as client:
            # Initiate resumable upload
            init_resp = client.post(
                YOUTUBE_UPLOAD_URL,
                params={"uploadType": "resumable", "part": "snippet,status"},
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "X-Upload-Content-Type": mime_type,
                    "X-Upload-Content-Length": str(file_size),
                    "Content-Type": "application/json",
                },
                content=json.dumps(metadata),
            )
            init_resp.raise_for_status()
            upload_url = init_resp.headers["Location"]

            # Upload the file
            with open(video_path, "rb") as f:
                upload_resp = client.put(
                    upload_url,
                    headers={
                        "Content-Type": mime_type,
                        "Content-Length": str(file_size),
                    },
                    content=f.read(),
                )
            upload_resp.raise_for_status()
            result = upload_resp.json()

        video_id = result["id"]

        # Set thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            self._set_thumbnail(video_id, thumbnail_path)

        return {
            "video_id": video_id,
            "url": f"https://youtu.be/{video_id}",
            "status": "uploaded",
            "title": title,
        }

    def _set_thumbnail(self, video_id: str, thumbnail_path: str):
        """Upload thumbnail for a video."""
        mime_type = mimetypes.guess_type(thumbnail_path)[0] or "image/jpeg"

        with httpx.Client(timeout=60) as client:
            with open(thumbnail_path, "rb") as f:
                resp = client.post(
                    f"{YOUTUBE_BASE_URL}/videos",
                    params={"videoId": video_id},
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": mime_type,
                    },
                    content=f.read(),
                )
            resp.raise_for_status()


if __name__ == "__main__":
    publisher = YouTubePublisher()
    result = publisher.publish(
        video_path="output/master.mp4",
        title="Boruto: Two Blue Vortex - Scene 1",
        description="AI-generated live-action adaptation",
        tags=["boruto", "ai", "film"],
        thumbnail_path="output/thumbnail.jpg",
    )
    print(json.dumps(result, indent=2))
