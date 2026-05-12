
_FALLBACK = (
    "[cyan]For more information, please visit[/cyan] "
    "[link=https://github.com/spaghetti-lover/stock-filter.git]https://github.com/spaghetti-lover/stock-filter.git[/link]"
)


def fetch_announcements() -> dict:
    """Fetch announcements from the upstream endpoint, falling back to a default line on error."""
    try:
        return {
            "announcements":  [_FALLBACK],
            "require_attention": True,
        }
    except Exception:
        return {
            "announcements": [_FALLBACK],
            "require_attention": False,
        }
