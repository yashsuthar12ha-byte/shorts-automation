"""
YouTube Uploader - Handles authentication and video upload to YouTube.
Uses the YouTube Data API v3.
"""
import os
import json
import pickle
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


class YouTubeUploader:
    """Handles YouTube authentication and video upload."""

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
              "https://www.googleapis.com/auth/youtube",
              "https://www.googleapis.com/auth/youtubepartner"]

    def __init__(self):
        self.credentials_path = self._get_credentials_path()
        self.token_path = self._get_token_path()
        self.service = None

    def _get_credentials_path(self) -> Path:
        """Get path to OAuth client secrets file."""
        env_path = os.getenv("AI_GAME_SHORTS_YOUTUBE_CLIENT_SECRET")
        if env_path:
            return Path(env_path)
        return Path("config/youtube_credentials.json")

    def _get_token_path(self) -> Path:
        """Get path to stored OAuth token."""
        env_path = os.getenv("AI_GAME_SHORTS_YOUTUBE_TOKEN")
        if env_path:
            return Path(env_path)
        return config.output_dir / "youtube_token.json"

    def authenticate(self) -> bool:
        """Authenticate with YouTube API. Returns True if successful."""
        credentials = None

        # Try loading saved token
        if self.token_path.exists():
            try:
                with open(self.token_path, "r") as f:
                    creds_data = json.load(f)
                credentials = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            except Exception as e:
                log.warning(f"Failed to load saved token: {e}")

        # Refresh if expired
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                log.info("YouTube token refreshed")
            except Exception as e:
                log.warning(f"Token refresh failed: {e}")
                credentials = None

        # New OAuth flow if no valid credentials
        if not credentials or not credentials.valid:
            if not self.credentials_path.exists():
                log.error(
                    "YouTube credentials not found!\n"
                    f"Place your OAuth client JSON at: {self.credentials_path}\n"
                    "Get credentials from: https://console.cloud.google.com/apis/credentials"
                )
                return False

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES
                )
                credentials = flow.run_local_server(
                    port=8080,
                    prompt="consent",
                    open_browser=True,
                )
                log.info("YouTube OAuth completed successfully")
            except Exception as e:
                log.error(f"OAuth failed: {e}")
                return False

            # Save token
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            creds_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }
            with open(self.token_path, "w") as f:
                json.dump(creds_data, f, indent=2)
            log.info(f"YouTube token saved to {self.token_path}")

        # Build service
        self.service = build("youtube", "v3", credentials=credentials)
        return True

    def upload_short(self, video_path: Path, title: str, description: str,
                     hashtags: str, privacy: Optional[str] = None,
                     thumbnail_path: Optional[Path] = None) -> Optional[str]:
        """
        Upload a Short to YouTube.
        Returns the video ID if successful.
        """
        if not self.service:
            if not self.authenticate():
                return None

        privacy = privacy or config.get("youtube", "upload", "privacy", default="public")

        # Build full description with hashtags
        full_description = description.strip()
        if hashtags:
            full_description += f"\n\n{hashtags}"

        # Check if dry run mode
        if os.getenv("AI_GAME_SHORTS_DRY_RUN", "false").lower() == "true":
            log.info(f"DRY RUN - Would upload: {title}")
            log.info(f"  File: {video_path}")
            log.info(f"  Description: {full_description[:100]}...")
            log.info(f"  Privacy: {privacy}")
            return "dry_run_video_id"

        try:
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": full_description[:5000],
                    "categoryId": self._get_category_id(),
                },
                "status": {
                    "privacyStatus": privacy,
                    "selfDeclaredMadeForKids": False,
                },
            }

            # Add to playlist if configured
            if config.get("youtube", "upload", "auto_playlist", default=True):
                playlist_name = config.get("youtube", "upload", "playlist_name",
                                            default="AI Generated Shorts")
                body["snippet"]["playlistId"] = self._get_or_create_playlist(playlist_name)

            media = MediaFileUpload(
                str(video_path),
                chunksize=-1,
                resumable=True,
            )

            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = request.execute()
            video_id = response.get("id")
            log.info(f"Uploaded: {title} -> https://youtu.be/{video_id}")

            # Upload thumbnail if available
            if thumbnail_path and thumbnail_path.exists():
                self._upload_thumbnail(video_id, thumbnail_path)

            return video_id

        except Exception as e:
            log.error(f"YouTube upload failed: {e}")
            return None

    def _get_category_id(self) -> str:
        """Get YouTube category ID for Gaming."""
        category_name = config.get("youtube", "upload", "category", default="Gaming")
        category_map = {
            "Gaming": "20",
            "Entertainment": "24",
            "Education": "27",
        }
        return category_map.get(category_name, "20")

    def _get_or_create_playlist(self, playlist_name: str) -> Optional[str]:
        """Get existing playlist ID or create a new one."""
        try:
            # Search for existing playlist
            request = self.service.playlists().list(
                part="snippet",
                mine=True,
            )
            response = request.execute()
            for item in response.get("items", []):
                if item["snippet"]["title"] == playlist_name:
                    return item["id"]

            # Create new playlist
            body = {
                "snippet": {
                    "title": playlist_name,
                    "description": "Auto-generated by AI Game Shorts",
                },
                "status": {
                    "privacyStatus": "public",
                },
            }
            response = self.service.playlists().insert(
                part="snippet,status",
                body=body,
            ).execute()
            return response.get("id")

        except Exception as e:
            log.warning(f"Playlist operation failed: {e}")
            return None

    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """Upload thumbnail for a video."""
        try:
            self.service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path)),
            ).execute()
            log.info(f"Thumbnail uploaded for video {video_id}")
            return True
        except Exception as e:
            log.warning(f"Thumbnail upload failed: {e}")
            return False

    def check_quota(self) -> dict:
        """Check remaining API quota (approximate)."""
        try:
            request = self.service.channels().list(
                part="statistics",
                mine=True,
            )
            response = request.execute()
            return response.get("items", [{}])[0].get("statistics", {})
        except Exception:
            return {}
