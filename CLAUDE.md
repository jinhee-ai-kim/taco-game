# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simple pygame-based game called "Taco Eating Game" where the player controls a character at the bottom of the screen to catch falling food items. Different food types award or deduct points.

## Running the Game

**Install dependencies:**
```bash
pip install pygame
```

**Run the game:**
```bash
python taco_game.py
```

**Controls:**
- Left/Right arrow keys: Move player
- ESC: Quit game

## Architecture

`taco_game.py` is a single-file game with a straightforward structure:

1. **Initialization**: Pygame setup, screen dimensions (800x600), colors, and fonts
2. **Player class**: Sprite-based character controlled via keyboard, positioned at bottom of screen
3. **Food class**: Sprite-based falling objects with three types:
   - Taco (green): +10 points
   - Donut (red): -5 points
   - Cake (orange): -3 points
4. **Main game loop**: Handles events, updates sprites, checks collisions, renders scene

The game uses pygame's sprite collision detection and a simple timer for spawning food at intervals.

## Customization Guide

**Game mechanics:**
- `spawn_interval` (line 102): Lower value = food spawns faster. Default: 30 frames
- `FPS` (line 24): Game speed in frames per second
- Food `points` values (lines 67, 70, 73): Adjust score awards/penalties

**Visual customization:**
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`: Change screen dimensions
- Color constants (lines 15-20): Modify BG_COLOR and food colors
- Player/food sizes (lines 33-34, 60-61): Change width/height values
- Player `speed` (line 40): Movement speed

**Adding images:**
Both Player and Food classes have comments indicating where to use `pygame.image.load()` to replace geometric shapes with PNG/JPG images. Replace the `pygame.draw.rect()` and `pygame.draw.circle()` calls in the `draw()` methods with `screen.blit()` calls.

**Food spawn weights:**
Line 121 defines food type probabilities. Adjust the `weights=[5, 2, 2]` list to change taco/donut/cake frequency (currently taco appears 5x more often than the others).

## Development Notes

- The game uses pygame sprite groups for efficient collision detection and rendering
- All game state (score, sprite positions, timers) is global; refactoring into a Game class would be a natural next step for larger features
- The main loop runs at 60 FPS with a fixed timestep via `clock.tick(FPS)`
