#!/usr/bin/env python3
import os
import sys

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def load_env():
    # Load .env.development.local first if available, then .env
    if load_dotenv is None:
        return
    if os.path.exists(".env.development.local"):
        load_dotenv(".env.development.local", override=False)
    else:
        load_dotenv()


def main() -> int:
    load_env()

    url = (
        os.getenv("KV_REST_API_URL")
        or os.getenv("UPSTASH_REDIS_REST_URL")
        or os.getenv("UPSTASH_REDIS_URL")
    )
    token = (
        os.getenv("KV_REST_API_TOKEN")
        or os.getenv("UPSTASH_REDIS_REST_TOKEN")
        or os.getenv("UPSTASH_REDIS_TOKEN")
    )

    if not url or not token:
        print(
            "Missing Upstash REST credentials. Set KV_REST_API_URL and KV_REST_API_TOKEN, "
            "or UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN, or create .env.development.local."
        )
        return 1

    try:
        from upstash_redis import Redis

        r = Redis(url=url, token=token)
        key = "quizmed:health"
        r.set(key, "ok", ex=60)
        val = r.get(key)
        print(f"Health check -> {key}={val!r}")
        return 0
    except Exception as e:
        print(f"Upstash test failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

