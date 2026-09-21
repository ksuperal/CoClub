"""UTM link generation and click tracking."""

from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from typing import Any


def generate_utm_link(
    *,
    base_url: str,
    campaign_id: str,
    platform: str,
    variant_id: str | None = None,
    post_id: str | None = None,
) -> str:
    """Generate a UTM-tagged link for social posts.

    Example output:
    https://yourstore.com/product/123?utm_source=instagram&utm_medium=social&utm_campaign=abc123&utm_content=variant_xyz
    """
    # Parse existing URL
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)

    # Add UTM parameters
    utm_params = {
        "utm_source": platform,
        "utm_medium": "social",
        "utm_campaign": campaign_id,
    }

    if variant_id:
        utm_params["utm_content"] = variant_id
    elif post_id:
        utm_params["utm_content"] = post_id

    # Merge with existing query params (flatten lists from parse_qs)
    for key, value in query_params.items():
        if isinstance(value, list) and len(value) > 0:
            query_params[key] = value[0]

    query_params.update(utm_params)

    # Rebuild URL
    new_query = urlencode(query_params)
    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return new_url


def extract_utm_params(url: str) -> dict[str, str | None]:
    """Extract UTM parameters from a URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    return {
        "utm_source": params.get("utm_source", [None])[0],
        "utm_medium": params.get("utm_medium", [None])[0],
        "utm_campaign": params.get("utm_campaign", [None])[0],
        "utm_content": params.get("utm_content", [None])[0],
    }


def shorten_url(long_url: str) -> str:
    """Shorten a URL for social media posts (optional enhancement).

    For now, just returns the URL as-is. You could integrate with:
    - bit.ly API
    - TinyURL API
    - Your own URL shortener
    """
    # TODO: Implement URL shortening if needed
    return long_url
