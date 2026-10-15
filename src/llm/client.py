"""Shared OpenAI-compatible client for the opencode Go inference API.

Endpoint: https://opencode.ai/inference/go/v1 (override with OPENCODE_BASE_URL)
Auth: OPENCODE_API_KEY environment variable.
Default model: deepseek-v4.1-flash
"""

import logging
import os
import time
import uuid

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

load_dotenv()

DEFAULT_MODEL = "deepseek-v4.1-flash"
DEFAULT_BASE_URL = "https://opencode.ai/inference/go/v1"
DEFAULT_USER_AGENT = "tiet-notegen/1.0"

_session_id = os.getenv("OPENCODE_SESSION_ID") or uuid.uuid4().hex


def get_session_id() -> str:
    return _session_id


def get_default_headers() -> dict[str, str]:
    return {
        "User-Agent": os.getenv("OPENCODE_USER_AGENT", DEFAULT_USER_AGENT),
        "x-opencode-session": get_session_id(),
    }


def get_base_url() -> str:
    return os.getenv("OPENCODE_BASE_URL", DEFAULT_BASE_URL)


def get_api_key() -> str | None:
    return os.getenv("OPENCODE_API_KEY")


def get_client(timeout: float = 120.0) -> OpenAI:
    return OpenAI(
        api_key=get_api_key(),
        base_url=get_base_url(),
        timeout=timeout,
        default_headers=get_default_headers(),
    )


def generate_text(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 5,
    base_delay: int = 5,
    **kwargs,
) -> str:
    """Call the opencode Go chat-completions API with retries/backoff.

    Retries on rate limits (429) and transient 5xx / connection errors.
    """
    client = get_client()
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                extra_headers=get_default_headers(),
                **kwargs,
            )
            content = response.choices[0].message.content
            return content or ""

        except RateLimitError as e:
            wait_time = base_delay * attempt
            logging.warning(
                f"Rate limited (429). Attempt {attempt}/{max_retries}. "
                f"Retrying in {wait_time}s... ({e})"
            )
            time.sleep(wait_time)

        except APIStatusError as e:
            status = e.status_code
            if status is not None and 500 <= status < 600 and attempt < max_retries:
                wait_time = base_delay * attempt
                logging.warning(
                    f"Server error ({status}). Attempt {attempt}/{max_retries}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                continue
            logging.error(f"API status error in generate_text: {e}")
            raise

        except APIConnectionError as e:
            wait_time = base_delay * attempt
            logging.warning(
                f"Connection error. Attempt {attempt}/{max_retries}. "
                f"Retrying in {wait_time}s... ({e})"
            )
            time.sleep(wait_time)

        except Exception as e:
            logging.error(f"Unexpected error in generate_text: {e}")
            raise

    raise RuntimeError(
        f"Failed to get response from model '{model}' after {max_retries} retries"
    )
