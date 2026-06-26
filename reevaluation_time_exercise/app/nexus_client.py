"""
Nexus API client - handles authentication, fetching user lessons,
and retrieving cohort user lists.
"""

import requests
import logging

log = logging.getLogger(__name__)

API_BASE = "https://api.hub.datascientest.com"


def authenticate(email: str, password: str) -> str | None:
    """
    Authenticate with Nexus and return the JWT access token.
    Returns None on failure.
    """
    resp = requests.post(
        f"{API_BASE}/auth/login/nexus",
        json={"email": email, "password": password},
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json().get("return", {}).get("access_token")
    return None


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def fetch_user_lessons(user_id: int, token: str) -> dict | list | None:
    """
    GET /users/{user_id}/lessons
    Returns the full JSON response (list of sprints with modules/exercises).
    Handles potential wrapping in a 'return' key.
    """
    try:
        resp = requests.get(
            f"{API_BASE}/users/{user_id}/lessons",
            headers=_headers(token),
            timeout=60,
        )
        log.info("Lessons API for user %s → status %s", user_id, resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            # Some Nexus endpoints wrap data in a "return" key
            if isinstance(data, dict) and "return" in data:
                data = data["return"]
            log.info("  → type=%s, top-keys=%s",
                     type(data).__name__,
                     list(data.keys()) if isinstance(data, dict) else f"list[{len(data)}]")
            return data
        else:
            log.warning("  → error body: %s", resp.text[:300])
    except Exception as e:
        log.error("Exception fetching lessons for user %s: %s", user_id, e)
    return None


def fetch_cohort_users(cohort_id: int, token: str) -> list[dict] | None:
    """
    GET /cohorts/{cohort_id}/users
    Returns the list of user dicts, or None on failure.
    """
    try:
        resp = requests.get(
            f"{API_BASE}/cohorts/{cohort_id}/users",
            headers=_headers(token),
            timeout=60,
        )
        log.info("Cohort users API for cohort %s → status %s", cohort_id, resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            log.info("  → type=%s, top-keys=%s",
                     type(data).__name__,
                     list(data.keys()) if isinstance(data, dict) else f"list[{len(data)}]")

            # Handle various response formats
            if isinstance(data, list):
                # Direct list of users
                log.info("  → direct list of %d users", len(data))
                return data
            elif isinstance(data, dict):
                # Could be wrapped in "return" or have "users" key
                if "return" in data:
                    inner = data["return"]
                    if isinstance(inner, list):
                        log.info("  → return-wrapped list of %d users", len(inner))
                        return inner
                    elif isinstance(inner, dict) and "users" in inner:
                        users = inner["users"]
                        log.info("  → return.users list of %d users", len(users))
                        return users
                if "users" in data:
                    users = data["users"]
                    log.info("  → users list of %d users", len(users))
                    return users
                # If it has an "id" field, it might be a single user
                if "id" in data:
                    log.info("  → single user object")
                    return [data]
            log.warning("  → unexpected format, returning None")
        else:
            log.warning("  → error body: %s", resp.text[:300])
    except Exception as e:
        log.error("Exception fetching cohort %s users: %s", cohort_id, e)
    return None
