"""Target profile registry for multi-target support.

Each profile defines credentials, login paths, and auth mechanisms for a target application.
Exploit step generators use the active profile to produce target-appropriate CAMRO steps.
"""

from typing import Literal, Optional

from pydantic import BaseModel


class TargetCredentials(BaseModel):
    username: str
    password: str


class TargetProfile(BaseModel):
    name: str
    default_url: str
    login_path: str
    auth_mechanism: Literal["bearer_token", "session_cookie"]
    user_a: TargetCredentials
    user_b: TargetCredentials
    login_body_fields: tuple[str, str]  # e.g. ("email", "password")
    token_extraction_pattern: Optional[str] = None  # bearer only
    session_cookie_name: Optional[str] = None  # cookie only
    csrf_token_pattern: Optional[str] = None  # DVWA only


TARGET_PROFILES: dict[str, TargetProfile] = {
    "juice_shop": TargetProfile(
        name="juice_shop",
        default_url="http://localhost:3000",
        login_path="/rest/user/login",
        auth_mechanism="bearer_token",
        user_a=TargetCredentials(username="admin@juice-sh.op", password="admin123"),
        user_b=TargetCredentials(username="jim@juice-sh.op", password="ncc-1701"),
        login_body_fields=("email", "password"),
        token_extraction_pattern=r'"token"\s*:\s*"([^"]+)"',
    ),
    "nodegoat": TargetProfile(
        name="nodegoat",
        default_url="http://localhost:4000",
        login_path="/login",
        auth_mechanism="session_cookie",
        user_a=TargetCredentials(username="user1", password="User1_123"),
        user_b=TargetCredentials(username="user2", password="User2_123"),
        login_body_fields=("userName", "password"),
        session_cookie_name="connect.sid",
    ),
    "dvwa": TargetProfile(
        name="dvwa",
        default_url="http://localhost:8081",
        login_path="/login.php",
        auth_mechanism="session_cookie",
        user_a=TargetCredentials(username="admin", password="password"),
        user_b=TargetCredentials(username="gordonb", password="abc123"),
        login_body_fields=("username", "password"),
        session_cookie_name="PHPSESSID",
        csrf_token_pattern=r'user_token.*?value=["\']([^"\']+)["\']',
    ),
}


def get_active_profile(name: str | None = None) -> TargetProfile:
    """Return the TargetProfile for the given name, defaulting to juice_shop."""
    key = name or "juice_shop"
    if key not in TARGET_PROFILES:
        raise ValueError(f"Unknown target profile: {key!r}. Available: {list(TARGET_PROFILES)}")
    return TARGET_PROFILES[key]
