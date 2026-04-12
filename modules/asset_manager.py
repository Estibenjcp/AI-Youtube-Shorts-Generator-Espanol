import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

# Reuse a single session with proper headers to reduce connection resets
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "AutoShorts/1.0 (video generator)",
    "Connection": "keep-alive",
})


class AssetManager:
    def __init__(self):
        self.api_key  = os.getenv("PEXELS_API_KEY", "")
        self.base_url = "https://api.pexels.com/videos/search"
        self.headers  = {"Authorization": self.api_key}
        self.assets_dir = os.path.join(os.getcwd(), "assets", "video_clips")
        os.makedirs(self.assets_dir, exist_ok=True)

    # ── Search ────────────────────────────────────────────────────────────────

    def search_video(self, query: str, duration_min: int = 4, _depth: int = 0) -> str | None:
        """
        Searches Pexels for a portrait video matching the query.
        Returns the download URL or None.
        """
        if _depth > 1:          # max one simplification retry
            return None

        print(f"   🔍 Searching Pexels for: '{query}'...")

        params = {
            "query":       query,
            "per_page":    8,
            "orientation": "portrait",
            "size":        "medium",
        }

        for attempt in range(3):
            try:
                resp = _SESSION.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=15,
                )
                if resp.status_code == 429:
                    wait = 10 * (attempt + 1)
                    print(f"      ⏳ Rate limited — waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if resp.status_code != 200:
                    print(f"      ⚠️ API Error: {resp.status_code}")
                    return None

                data = resp.json()
                break

            except Exception as e:
                wait = 3 * (attempt + 1)
                print(f"      ⚠️ Search attempt {attempt+1}/3 failed: {e} — retrying in {wait}s")
                time.sleep(wait)
        else:
            return None

        if not data.get("videos"):
            if " " in query:
                simple = query.split()[-1]
                print(f"      ⚠️ No results. Retrying with '{simple}'...")
                time.sleep(1)
                return self.search_video(simple, duration_min, _depth + 1)
            return None

        valid = [v for v in data["videos"] if v["duration"] >= duration_min]
        if not valid:
            valid = data["videos"]

        chosen     = random.choice(valid)
        vid_files  = sorted(chosen["video_files"], key=lambda x: x["width"] * x["height"], reverse=True)
        return vid_files[0]["link"]

    # ── Download ──────────────────────────────────────────────────────────────

    def download_video(self, url: str, filename: str, retries: int = 3) -> str | None:
        """
        Downloads a video with retry + exponential backoff.
        """
        save_path = os.path.join(self.assets_dir, filename)

        if os.path.exists(save_path):
            return save_path

        for attempt in range(retries):
            try:
                with _SESSION.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(save_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            f.write(chunk)
                return save_path

            except Exception as e:
                wait = 4 * (2 ** attempt)   # 4s, 8s, 16s
                print(f"      ⚠️ Download attempt {attempt+1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    print(f"         Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"      ❌ Failed to download {filename} after {retries} attempts.")

        # Clean up partial file if it exists
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except Exception:
                pass
        return None

    # ── Orchestrate ───────────────────────────────────────────────────────────

    def get_videos(self, script_data: list) -> list:
        """
        Downloads TWO or THREE videos per scene (A, B, and optional C for testimonio mode).
        Returns a list of tuples: (path_a, path_b) or (path_a, path_b, path_c).
        """
        print("🎥 Starting Video Download...")
        video_pairs = []

        for scene in script_data:
            scene_id = scene["id"]
            query_a  = scene.get("visual_1", scene.get("keywords", "abstract"))
            query_b  = scene.get("visual_2", query_a)
            query_c  = scene.get("visual_3", None)

            # Search A
            url_a  = self.search_video(query_a)
            path_a = self.download_video(url_a, f"scene_{scene_id}_a.mp4") if url_a else None
            time.sleep(1.5)

            # Search B
            url_b  = self.search_video(query_b)
            path_b = self.download_video(url_b, f"scene_{scene_id}_b.mp4") if url_b else None

            # Search C (only if visual_3 exists)
            path_c = None
            if query_c:
                time.sleep(1.5)
                url_c  = self.search_video(query_c)
                path_c = self.download_video(url_c, f"scene_{scene_id}_c.mp4") if url_c else None

            # Self-healing fallbacks
            if not path_a and path_b:
                path_a = path_b
            if not path_b and path_a:
                path_b = path_a
            if path_c is None and path_a:
                pass  # C is optional, no fallback needed

            if path_a and path_b:
                if path_c:
                    video_pairs.append((path_a, path_b, path_c))
                    print(f"   ✅ Scene {scene_id} Ready (A + B + C).")
                else:
                    video_pairs.append((path_a, path_b))
                    print(f"   ✅ Scene {scene_id} Ready (A + B).")
            else:
                print(f"   ❌ Scene {scene_id} Completely Failed.")
                video_pairs.append(None)

            time.sleep(1)

        return video_pairs
