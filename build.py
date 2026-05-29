"""Build script. Run: python build.py  then  python -m pygbag ."""
import subprocess, sys, shutil
from pathlib import Path

ROOT      = Path(__file__).parent
TMPL_HASH = "27613e24ba16d44f2a5c88150c6d64e5"
TMPL_FILE = ROOT / "build" / "web-cache" / f"{TMPL_HASH}.tmpl"

# 1. Inject our custom loading screen as pygbag's template
#    pygbag reads this cache file instead of re-downloading from CDN
TMPL_FILE.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "docs" / "index.html", TMPL_FILE)

# 2. Build
result = subprocess.run([sys.executable, "-m", "pygbag", "--build", "."])
if result.returncode != 0:
    sys.exit(result.returncode)

# 3. background images must be in build/web/ so python -m pygbag . can serve them
shutil.copy(ROOT / "docs" / "bg_img.png",        ROOT / "build" / "web" / "bg_img.png")
shutil.copy(ROOT / "docs" / "bg_mobile_img.png", ROOT / "build" / "web" / "bg_mobile_img.png")

# 4. Update docs/ archives for GitHub Pages deployment
shutil.copy(ROOT / "build" / "web" / "tacoman.apk",   ROOT / "docs" / "tacoman.apk")
shutil.copy(ROOT / "build" / "web" / "tacoman.tar.gz", ROOT / "docs" / "tacoman.tar.gz")

print("Done. Local test: python -m pygbag .")
print("Deploy:           git push")
