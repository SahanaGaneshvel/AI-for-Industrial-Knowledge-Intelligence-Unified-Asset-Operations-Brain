"""Rate-limited Gemini API client wrapper with caching."""

import json
import hashlib
import time
import random
from pathlib import Path
from typing import Optional, Any
import google.generativeai as genai

from .config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    CACHE_DIR,
    MIN_REQUEST_INTERVAL,
    MAX_RETRIES,
    INITIAL_BACKOFF,
    MAX_BACKOFF,
)


class RateLimitedGeminiClient:
    """Gemini API client with rate limiting, caching, and exponential backoff."""

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it to your Google Gemini API key."
            )
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.last_request_time = 0.0
        self._cache_dir = CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """Generate cache key from prompt and optional image."""
        content = prompt.encode("utf-8")
        if image_data:
            content += image_data
        return hashlib.sha256(content).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Retrieve cached response if available."""
        cache_file = self._cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f).get("response")
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _cache_response(self, cache_key: str, response: str) -> None:
        """Cache response to disk."""
        cache_file = self._cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"response": response, "timestamp": time.time()}, f)
        except IOError:
            pass  # Silently fail caching

    def _wait_for_rate_limit(self) -> None:
        """Wait if needed to respect rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()

    def generate(
        self,
        prompt: str,
        image_data: Optional[bytes] = None,
        image_mime_type: str = "image/png",
        use_cache: bool = True,
        json_mode: bool = False,
    ) -> str:
        """Generate response with rate limiting, caching, and retry logic.

        Args:
            prompt: The text prompt to send
            image_data: Optional image bytes for vision requests
            image_mime_type: MIME type of the image
            use_cache: Whether to use/update cache
            json_mode: Whether to request JSON output

        Returns:
            Generated text response
        """
        # Check cache first
        cache_key = self._get_cache_key(prompt, image_data)
        if use_cache:
            cached = self._get_cached_response(cache_key)
            if cached:
                return cached

        # Prepare content
        content = []
        if image_data:
            content.append({
                "mime_type": image_mime_type,
                "data": image_data
            })
        content.append(prompt)

        # Configure generation
        generation_config = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        # Retry loop with exponential backoff
        backoff = INITIAL_BACKOFF
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                self._wait_for_rate_limit()

                response = self.model.generate_content(
                    content,
                    generation_config=generation_config if generation_config else None,
                )

                result = response.text

                # Cache successful response
                if use_cache:
                    self._cache_response(cache_key, result)

                return result

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if it's a rate limit error (429)
                if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                    # Add jitter to backoff
                    jitter = random.uniform(0, backoff * 0.1)
                    sleep_time = min(backoff + jitter, MAX_BACKOFF)
                    print(f"Rate limited. Retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(sleep_time)
                    backoff *= 2
                else:
                    # For other errors, shorter backoff
                    time.sleep(INITIAL_BACKOFF)

        raise RuntimeError(f"Failed after {MAX_RETRIES} retries. Last error: {last_error}")

    def extract_json(
        self,
        prompt: str,
        image_data: Optional[bytes] = None,
        image_mime_type: str = "image/png",
        use_cache: bool = True,
    ) -> dict:
        """Generate and parse JSON response.

        Args:
            prompt: The text prompt (should request JSON output)
            image_data: Optional image bytes
            image_mime_type: MIME type of image
            use_cache: Whether to use cache

        Returns:
            Parsed JSON as dict
        """
        response = self.generate(
            prompt=prompt,
            image_data=image_data,
            image_mime_type=image_mime_type,
            use_cache=use_cache,
            json_mode=True,
        )

        # Try to parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    return json.loads(response[start:end].strip())
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end > start:
                    return json.loads(response[start:end].strip())

            # Retry once on parse failure
            print("JSON parse failed, retrying extraction...")
            response = self.generate(
                prompt=prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no other text.",
                image_data=image_data,
                image_mime_type=image_mime_type,
                use_cache=False,
                json_mode=True,
            )
            return json.loads(response)


# Singleton instance
_client: Optional[RateLimitedGeminiClient] = None


def get_llm_client() -> RateLimitedGeminiClient:
    """Get or create the singleton LLM client."""
    global _client
    if _client is None:
        _client = RateLimitedGeminiClient()
    return _client


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text using Gemini embedding model."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']


# Alias for backward compatibility
GeminiClient = RateLimitedGeminiClient
