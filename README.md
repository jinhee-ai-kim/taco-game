# 🌮 Tacoman Game

A browser-based arcade game built with Python + Pygame, compiled to WebAssembly via Pygbag.  
Catch falling tacos, dodge snakes and spiders, and rack up 1000 points to win!

**[▶ Play in Browser](https://jinhee-ai-kim.github.io/taco-game/)**

---

## Gameplay

| Item | Effect |
|------|--------|
| 🌮 Taco | +10 points |
| 🌮 Giant Taco | +50 points + LUCKY flash |
| 🥤 Milkshake | +20 points + BOOST mode (taco rain!) |
| 🕷 Spider | -1 life + DANGER flash |
| 🐍 Snake | -1 life + DANGER flash |

- **Goal:** reach 1000 points before losing all 5 lives
- **Controls:**
  - **PC:** `←` / `→` arrow keys, or click and drag
  - **Mobile:** drag your finger left/right to move the player

---

## Run Locally

### Desktop (pygame window)

**Requirements:** Python 3.12, pygame 2.6+

```bash
pip install pygame
python main.py
```

### Browser (test the web build locally)

```bash
python build.py        # build + inject custom loading screen
python -m pygbag .     # serve at http://localhost:8000
```

### Start the game

```bash
python main.py
```

---

## Build for Web (GitHub Pages)

### Requirements

- pygbag 0.9.3

```bash
pip install pygbag==0.9.3
```

### Build

Run this from the **project root** (the folder that contains `main.py`):

```bash
python -m pygbag --build .
```

Output files are written to `build/web/`. Copy the two archive files to `docs/`:

```bash
# Windows
copy build\web\tacoman.apk docs\tacoman.apk
copy build\web\tacoman.tar.gz docs\tacoman.tar.gz

# macOS / Linux
cp build/web/tacoman.apk docs/tacoman.apk
cp build/web/tacoman.tar.gz docs/tacoman.tar.gz
```

Then commit and push — GitHub Pages will serve the updated game from `docs/`.

> **Note:** Do **not** overwrite `docs/index.html` from the build output.  
> The one in `docs/` has custom mobile viewport settings that the template version lacks.

### Enable GitHub Pages

1. Go to your repo → **Settings** → **Pages**
2. Set **Source** to `Deploy from a branch`
3. Set **Branch** to `main`, folder to `/docs`
4. Save — your game will be live at `https://<your-username>.github.io/<repo-name>/`

---

## Project Structure

```
tacoman/
├── main.py                  # Game source
├── assets/
│   ├── img/tacoman/         # Sprites (pacman, taco, snake, ...)
│   └── sound/               # OGG audio files
├── docs/                    # GitHub Pages deployment
│   ├── index.html           # Web shell (do not overwrite from build)
│   ├── tacoman.tar.gz       # Packed game (update after each build)
│   └── tacoman.apk          # Packed game for itch.io
└── build/web/               # pygbag build output (not committed)
```
