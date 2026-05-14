import asyncio
from urllib.parse import urlparse, parse_qs

from fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

mcp = FastMCP(name="youtube")


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/").split("?")[0] or None
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("embed", "v", "shorts"):
            return parts[1]
    return None


@mcp.tool
async def get_youtube_transcript(url: str, languages: list[str] | None = None) -> dict:
    """Fetch the full transcript of a YouTube video given its URL.

    Args:
        url: Full YouTube video URL, e.g. https://www.youtube.com/watch?v=VIDEO_ID
        languages: Language codes in priority order. Defaults to ['vi', 'en'].
    """
    video_id = _extract_video_id(url)
    if not video_id:
        return {"error": f"Could not extract video ID from: {url}"}

    if languages is None:
        languages = ["vi", "en"]

    def _fetch():
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id, languages=languages)
        return {
            "video_id": video_id,
            "url": url,
            "language": fetched.language,
            "language_code": fetched.language_code,
            "is_generated": fetched.is_generated,
            "transcript": " ".join(s.text for s in fetched),
            "snippet_count": len(fetched),
        }

    try:
        return await asyncio.to_thread(_fetch)
    except TranscriptsDisabled:
        return {"error": f"Transcripts are disabled for video {video_id}"}
    except NoTranscriptFound:
        return {"error": f"No transcript found in languages {languages} for video {video_id}"}
    except VideoUnavailable:
        return {"error": f"Video {video_id} is unavailable"}
    except Exception as exc:
        return {"error": f"Failed to fetch transcript for {video_id}: {exc}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
