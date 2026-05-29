# -*- coding: utf-8 -*-
import pygame
import random
import sys
import asyncio
import os

if os.path.exists("assets/img/tacoman"):
    ASSET_PATH = "assets/img/tacoman"
    SOUND_PATH = "assets/sound"
else:
    ASSET_PATH = "img/tacoman"
    SOUND_PATH = "sound"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
YELLOW = (255, 220, 0)
PURPLE = (150, 0, 200)
WARNING_DURATION = 45
BOOST_DURATION = 120


class Player(pygame.sprite.Sprite):
    def __init__(self, pacman_img, pacman_close_img, red_pacman_img):
        super().__init__()
        self.pacman_img = pacman_img
        self.pacman_close_img = pacman_close_img
        self.red_pacman_img = red_pacman_img
        self.width = 90
        self.height = 90
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 10
        self.hurt_timer = 0
        self.eat_timer = 0
        self.touch_x = None  # None = no touch, int = active touch X coord

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

        if self.touch_x is not None:
            new_cx = max(
                self.width // 2, min(SCREEN_WIDTH - self.width // 2, self.touch_x)
            )
            self.rect.centerx = new_cx

        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        if self.eat_timer > 0:
            self.eat_timer -= 1

    def draw(self, surface):
        if self.hurt_timer > 0:
            img = self.red_pacman_img
        elif self.eat_timer > 0:
            img = self.pacman_close_img
        else:
            img = self.pacman_img
        surface.blit(img, self.rect)


class Food(pygame.sprite.Sprite):
    def __init__(self, food_type, images, start_y=None):
        super().__init__()
        self.food_type = food_type
        self.width = 60
        self.height = 60

        if food_type == "taco":
            self.image = images["taco"].copy()
            self.points = 10
        elif food_type == "giant_taco":
            self.width = 120
            self.height = 120
            self.image = images["giant_taco"].copy()
            self.points = 50
        elif food_type == "milkshake":
            self.height = 82
            key = random.choice(["milkshake", "oreo_milkshake"])
            self.image = images[key].copy()
            self.points = 20
        elif food_type == "spider":
            self.image = images["spider"].copy()
            self.points = 0
        else:
            self.image = images["snake"].copy()
            self.points = 0

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.rect.y = start_y if start_y is not None else random.randint(-100, -40)
        self.speed = 2 if food_type == "giant_taco" else random.randint(2, 5)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self, surface):
        surface.blit(self.image, self.rect)


def draw_lives(surface, bad_count, heart_red, heart_gray):
    for i in range(5):
        img = heart_gray if i >= (5 - bad_count) else heart_red
        x = SCREEN_WIDTH - 260 + i * 46
        surface.blit(img, (x, 14))


def draw_boost_flash(surface, timer, font_large, flash_surf):
    flash_surf.fill((0, 0, 0, 0))
    alpha = int(180 * abs((timer % 20) - 10) / 10)
    border = 22
    color = (255, 220, 0, alpha)
    pygame.draw.rect(flash_surf, color, (0, 0, SCREEN_WIDTH, border))
    pygame.draw.rect(
        flash_surf, color, (0, SCREEN_HEIGHT - border, SCREEN_WIDTH, border)
    )
    pygame.draw.rect(flash_surf, color, (0, 0, border, SCREEN_HEIGHT))
    pygame.draw.rect(
        flash_surf, color, (SCREEN_WIDTH - border, 0, border, SCREEN_HEIGHT)
    )
    surface.blit(flash_surf, (0, 0))
    text_color = YELLOW if (timer // 6) % 2 == 0 else WHITE
    boost_surf = font_large.render("BOOST!", True, text_color)
    surface.blit(
        boost_surf,
        (SCREEN_WIDTH // 2 - boost_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 40),
    )


LUCKY_DURATION = 90
RAINBOW_COLORS = [
    (255, 0, 0),
    (255, 127, 0),
    (255, 255, 0),
    (0, 200, 0),
    (0, 0, 255),
    (148, 0, 211),
]


def draw_lucky_flash(surface, timer, font_large, flash_surf):
    flash_surf.fill((0, 0, 0, 0))
    border = 26
    color_idx = (timer // 5) % len(RAINBOW_COLORS)
    r, g, b = RAINBOW_COLORS[color_idx]
    alpha = int(200 * abs((timer % 20) - 10) / 10)
    pygame.draw.rect(flash_surf, (r, g, b, alpha), (0, 0, SCREEN_WIDTH, border))
    pygame.draw.rect(
        flash_surf, (r, g, b, alpha), (0, SCREEN_HEIGHT - border, SCREEN_WIDTH, border)
    )
    pygame.draw.rect(flash_surf, (r, g, b, alpha), (0, 0, border, SCREEN_HEIGHT))
    pygame.draw.rect(
        flash_surf, (r, g, b, alpha), (SCREEN_WIDTH - border, 0, border, SCREEN_HEIGHT)
    )
    surface.blit(flash_surf, (0, 0))
    text_r, text_g, text_b = RAINBOW_COLORS[(timer // 3) % len(RAINBOW_COLORS)]
    lucky_surf = font_large.render("LUCKY!", True, (text_r, text_g, text_b))
    surface.blit(
        lucky_surf,
        (SCREEN_WIDTH // 2 - lucky_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 40),
    )


def draw_warning_flash(surface, timer, font_large, flash_surf):
    flash_surf.fill((0, 0, 0, 0))
    alpha = int(200 * (timer / WARNING_DURATION))
    border = 18
    pygame.draw.rect(flash_surf, (220, 20, 60, alpha), (0, 0, SCREEN_WIDTH, border))
    pygame.draw.rect(
        flash_surf,
        (220, 20, 60, alpha),
        (0, SCREEN_HEIGHT - border, SCREEN_WIDTH, border),
    )
    pygame.draw.rect(flash_surf, (220, 20, 60, alpha), (0, 0, border, SCREEN_HEIGHT))
    pygame.draw.rect(
        flash_surf,
        (220, 20, 60, alpha),
        (SCREEN_WIDTH - border, 0, border, SCREEN_HEIGHT),
    )
    surface.blit(flash_surf, (0, 0))
    if (timer // 6) % 2 == 0:
        warn_surf = font_large.render("DANGER!", True, RED)
        surface.blit(
            warn_surf,
            (SCREEN_WIDTH // 2 - warn_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 40),
        )


def draw_start_screen(surface, font_large, font_mid, font_small, bg_image):
    surface.blit(bg_image, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    surface.blit(overlay, (0, 0))

    title_text = font_large.render("Tacoman Game", True, YELLOW)
    surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 220))

    btn_w, btn_h = 300, 70
    btn_x = SCREEN_WIDTH // 2 - btn_w // 2
    btn_y = 360
    pygame.draw.rect(surface, GREEN, (btn_x, btn_y, btn_w, btn_h), border_radius=12)
    pygame.draw.rect(surface, WHITE, (btn_x, btn_y, btn_w, btn_h), 3, border_radius=12)
    btn_text = font_mid.render("Start Game", True, WHITE)
    surface.blit(
        btn_text,
        (
            SCREEN_WIDTH // 2 - btn_text.get_width() // 2,
            btn_y + (btn_h - btn_text.get_height()) // 2,
        ),
    )

    hint_text = font_small.render("Reach 1000 points as fast as you can!", True, (200, 200, 200))
    surface.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, 460))

    touch_hint = font_small.render("Watch out for spiders and snakes!", True, (160, 200, 160))
    surface.blit(touch_hint, (SCREEN_WIDTH // 2 - touch_hint.get_width() // 2, 505))

    return pygame.Rect(btn_x, btn_y, btn_w, btn_h)


RESTART_BTN_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 150, 500, 300, 65)


def draw_restart_button(surface, font_mid):
    pygame.draw.rect(surface, GREEN, RESTART_BTN_RECT, border_radius=12)
    pygame.draw.rect(surface, WHITE, RESTART_BTN_RECT, 3, border_radius=12)
    btn_text = font_mid.render("Restart", True, WHITE)
    surface.blit(
        btn_text,
        (
            RESTART_BTN_RECT.centerx - btn_text.get_width() // 2,
            RESTART_BTN_RECT.centery - btn_text.get_height() // 2,
        ),
    )


def draw_win_screen(surface, seconds, score, font_large, font_mid, font_small):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    win_text = font_large.render("YOU WIN!", True, YELLOW)
    surface.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, 200))
    time_text = font_mid.render(f"Clear Time: {seconds}s", True, WHITE)
    surface.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, 300))
    score_text = font_mid.render(f"Final Score: {score}", True, WHITE)
    surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 370))
    draw_restart_button(surface, font_mid)
    quit_text = font_small.render("ESC: Quit", True, (180, 180, 180))
    surface.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 590))


def draw_lose_screen(surface, score, font_large, font_mid, font_small):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    lose_text = font_large.render("GAME OVER", True, RED)
    surface.blit(lose_text, (SCREEN_WIDTH // 2 - lose_text.get_width() // 2, 240))
    score_text = font_mid.render(f"Score: {score}", True, WHITE)
    surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 355))
    draw_restart_button(surface, font_mid)
    quit_text = font_small.render("ESC: Quit", True, (180, 180, 180))
    surface.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 590))


def _check_web_start():
    """Return True if the HTML start button was clicked (web mode only)."""
    try:
        import platform

        return bool(platform.window.game_should_start)
    except Exception:
        return False


async def main():
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()
    pygame.mixer.set_num_channels(16)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Taco Eating Game")

    # Hide the HTML loading overlay now that pygame canvas is ready (web mode)
    try:
        import platform as _plt

        _plt.window.loadingScreen_hide()
    except Exception:
        pass

    clock = pygame.time.Clock()
    FPS = 60
    font_large = pygame.font.Font(None, 74)
    font_mid = pygame.font.Font(None, 58)
    font_small = pygame.font.Font(None, 44)

    await asyncio.sleep(0)  # yield before image loading

    pygame.mixer.music.load(f"{SOUND_PATH}/bg_sound.ogg")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

    eat_taco_sound = pygame.mixer.Sound(f"{SOUND_PATH}/eat_taco_sound.ogg")
    eat_snake_sound = pygame.mixer.Sound(f"{SOUND_PATH}/eat_snake_sound.ogg")
    boost_sound = pygame.mixer.Sound(f"{SOUND_PATH}/boost_sound.ogg")
    powerup_sound = pygame.mixer.Sound(f"{SOUND_PATH}/power_up_sound.ogg")
    fail_sound = pygame.mixer.Sound(f"{SOUND_PATH}/fail_sound.ogg")
    win_sound = pygame.mixer.Sound(f"{SOUND_PATH}/win_sound.ogg")

    eat_taco_sound.set_volume(0.6)
    eat_snake_sound.set_volume(0.7)
    boost_sound.set_volume(0.7)
    powerup_sound.set_volume(0.8)

    bg_image = pygame.image.load(f"{ASSET_PATH}/bg_img.png")
    bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    images = {
        "taco": pygame.transform.scale(
            pygame.image.load(f"{ASSET_PATH}/taco.png"), (60, 60)
        ),
        "giant_taco": pygame.transform.scale(
            pygame.image.load(f"{ASSET_PATH}/taco.png"), (120, 120)
        ),
        "milkshake": pygame.transform.scale(
            pygame.image.load(f"{ASSET_PATH}/milkshake.png"), (60, 82)
        ),
        "oreo_milkshake": pygame.transform.scale(
            pygame.image.load(f"{ASSET_PATH}/oreo_milkshake.png"), (60, 82)
        ),
        "spider": pygame.transform.scale(
            pygame.image.load(f"{ASSET_PATH}/spider.png"), (60, 60)
        ),
        "snake": pygame.transform.scale(
            pygame.image.load(f"{ASSET_PATH}/snake.png"), (60, 60)
        ),
    }
    heart_red = pygame.transform.scale(
        pygame.image.load(f"{ASSET_PATH}/red_heart.png"), (38, 38)
    )
    heart_gray = pygame.transform.scale(
        pygame.image.load(f"{ASSET_PATH}/gray_heart.png"), (38, 38)
    )
    pacman_img = pygame.transform.scale(
        pygame.image.load(f"{ASSET_PATH}/tx_pacman.png"), (90, 90)
    )
    pacman_close_img = pygame.transform.scale(
        pygame.image.load(f"{ASSET_PATH}/tx_pacman_close.png"), (90, 90)
    )
    red_pacman_img = pygame.transform.scale(
        pygame.image.load(f"{ASSET_PATH}/tx_red_pacman.png"), (90, 90)
    )

    score = 0
    bad_count = 0
    boost_active = False
    boost_timer = 0
    boost_spawn_count = 0
    warning_timer = 0
    lucky_timer = 0
    game_state = "start"
    elapsed_seconds = 0
    spawn_timer = 0
    spawn_interval = 30
    start_ticks = 0

    player_group = pygame.sprite.Group()
    food_group = pygame.sprite.Group()
    player = Player(pacman_img, pacman_close_img, red_pacman_img)
    player_group.add(player)

    flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    start_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 360, 300, 70)

    DRAG_THRESHOLD = 12  # pixels of movement before drag is recognized
    _touch_start_x = 0
    _is_dragging = False

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN and game_state == "start":
                    powerup_sound.play()
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                    player.touch_x = None
                elif event.key == pygame.K_RETURN and game_state in ("win", "lose"):
                    powerup_sound.play()
                    score, bad_count = 0, 0
                    boost_active, boost_timer, boost_spawn_count = False, 0, 0
                    warning_timer, lucky_timer, spawn_timer = 0, 0, 0
                    food_group.empty()
                    player.rect.centerx = SCREEN_WIDTH // 2
                    player.hurt_timer, player.eat_timer = 0, 0
                    player.touch_x = None
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()

            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0] and game_state == "playing":
                    if not _is_dragging:
                        if abs(event.pos[0] - _touch_start_x) > DRAG_THRESHOLD:
                            _is_dragging = True
                    if _is_dragging:
                        player.touch_x = event.pos[0]

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                _touch_start_x = event.pos[0]
                _is_dragging = False
                if game_state == "start" and start_btn_rect.collidepoint(event.pos):
                    powerup_sound.play()
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                    player.touch_x = None
                elif game_state in ("win", "lose") and RESTART_BTN_RECT.collidepoint(
                    event.pos
                ):
                    powerup_sound.play()
                    score, bad_count = 0, 0
                    boost_active, boost_timer, boost_spawn_count = False, 0, 0
                    warning_timer, lucky_timer, spawn_timer = 0, 0, 0
                    food_group.empty()
                    player.rect.centerx = SCREEN_WIDTH // 2
                    player.hurt_timer, player.eat_timer = 0, 0
                    player.touch_x = None
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                player.touch_x = None
                _is_dragging = False

            elif event.type == pygame.FINGERDOWN:
                fx = int(event.x * SCREEN_WIDTH)
                fy = int(event.y * SCREEN_HEIGHT)
                _touch_start_x = fx
                _is_dragging = False
                if game_state == "start" and start_btn_rect.collidepoint(fx, fy):
                    powerup_sound.play()
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()
                    player.touch_x = None
                elif game_state in ("win", "lose") and RESTART_BTN_RECT.collidepoint(
                    fx, fy
                ):
                    powerup_sound.play()
                    score, bad_count = 0, 0
                    boost_active, boost_timer, boost_spawn_count = False, 0, 0
                    warning_timer, lucky_timer, spawn_timer = 0, 0, 0
                    food_group.empty()
                    player.rect.centerx = SCREEN_WIDTH // 2
                    player.hurt_timer, player.eat_timer = 0, 0
                    player.touch_x = None
                    game_state = "playing"
                    start_ticks = pygame.time.get_ticks()

            elif event.type == pygame.FINGERMOTION:
                if game_state == "playing":
                    fx = int(event.x * SCREEN_WIDTH)
                    if not _is_dragging:
                        if abs(fx - _touch_start_x) > DRAG_THRESHOLD:
                            _is_dragging = True
                    if _is_dragging:
                        player.touch_x = fx

            elif event.type == pygame.FINGERUP:
                player.touch_x = None
                _is_dragging = False

        if game_state == "start":
            # Web: HTML start button clicked - skip pygame start screen
            if _check_web_start():
                powerup_sound.play()
                game_state = "playing"
                start_ticks = pygame.time.get_ticks()
                player.touch_x = None
            else:
                draw_start_screen(screen, font_large, font_mid, font_small, bg_image)
                pygame.display.flip()
                await asyncio.sleep(0)
                continue

        if game_state == "playing":
            spawn_timer += 1
            if spawn_timer >= spawn_interval:
                food_types = ["taco", "spider", "snake", "milkshake", "giant_taco"]
                food_type = random.choices(food_types, weights=[6, 2, 2, 1, 1])[0]
                food_group.add(Food(food_type, images))
                spawn_timer = 0

            if boost_active:
                boost_timer -= 1
                if boost_spawn_count > 0 and spawn_timer % 4 == 0:
                    for _ in range(2):
                        food_group.add(
                            Food("taco", images, start_y=random.randint(-80, -20))
                        )
                    boost_spawn_count -= 1
                if boost_timer <= 0:
                    boost_active = False
                    boost_spawn_count = 0

            if warning_timer > 0:
                warning_timer -= 1
            if lucky_timer > 0:
                lucky_timer -= 1

            player_group.update()
            food_group.update()

            player_hitbox = player.rect.inflate(-20, -20)
            for food in list(food_group):
                food_hitbox = food.rect.inflate(-20, -20)
                if player_hitbox.colliderect(food_hitbox):
                    if food.food_type == "giant_taco":
                        score += food.points
                        player.eat_timer = 12
                        lucky_timer = LUCKY_DURATION
                        powerup_sound.play()
                    elif food.food_type == "taco":
                        score += food.points
                        player.eat_timer = 12
                        eat_taco_sound.stop()
                        eat_taco_sound.play()
                    elif food.food_type == "milkshake":
                        score += food.points
                        player.eat_timer = 12
                        boost_active = True
                        boost_timer = BOOST_DURATION
                        boost_spawn_count = 8
                        boost_sound.play()
                    elif food.food_type in ("spider", "snake"):
                        bad_count += 1
                        warning_timer = WARNING_DURATION
                        player.hurt_timer = 60
                        eat_snake_sound.play()
                    food.kill()

            if score >= 1000:
                game_state = "win"
                elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
                win_sound.play()
            elif bad_count >= 5:
                game_state = "lose"
                fail_sound.play()

        screen.blit(bg_image, (0, 0))

        if game_state == "playing":
            player.draw(screen)
            for food in food_group:
                food.draw(screen)
            score_text = font_large.render(f"Score: {score}", True, BLACK)
            screen.blit(score_text, (20, 15))
            draw_lives(screen, bad_count, heart_red, heart_gray)
            if warning_timer > 0:
                draw_warning_flash(screen, warning_timer, font_large, flash_surface)
            if lucky_timer > 0:
                draw_lucky_flash(screen, lucky_timer, font_large, flash_surface)
            if boost_active:
                draw_boost_flash(screen, boost_timer, font_large, flash_surface)

        elif game_state == "win":
            player.draw(screen)
            for food in food_group:
                food.draw(screen)
            draw_win_screen(
                screen, elapsed_seconds, score, font_large, font_mid, font_small
            )

        elif game_state == "lose":
            player.draw(screen)
            for food in food_group:
                food.draw(screen)
            draw_lose_screen(screen, score, font_large, font_mid, font_small)

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
