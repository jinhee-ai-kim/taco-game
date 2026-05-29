# -*- coding: utf-8 -*-
import pygame
import random
import asyncio
import os

if os.path.exists("assets/img/tacoman"):
    ASSET_PATH = "assets/img/tacoman"
    SOUND_PATH = "assets/sound"
else:
    ASSET_PATH = "img/tacoman"
    SOUND_PATH = "sound"


def _is_mobile():
    try:
        import platform
        return bool(platform.window.TACOMAN_MOBILE)
    except Exception:
        return False


MOBILE = _is_mobile()
SCREEN_WIDTH  = 360  if MOBILE else 1280
SCREEN_HEIGHT = 640  if MOBILE else 720
FPS           = 60

# sprite / UI scale constants (mobile vs desktop)
_SP  = 55  if MOBILE else 90    # player sprite size
_SF  = 38  if MOBILE else 60    # food sprite size
_SFG = 76  if MOBILE else 120   # giant taco size
_SH  = 22  if MOBILE else 38    # heart size
_FL  = 26  if MOBILE else 74    # font large
_FM  = 21  if MOBILE else 58    # font mid
_FS  = 15  if MOBILE else 44    # font small
_BORDER_WARN  =  8 if MOBILE else 18
_BORDER_BOOST = 10 if MOBILE else 22
_BORDER_LUCKY = 12 if MOBILE else 26

WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
GREEN  = (34, 139, 34)
RED    = (220, 20, 60)
YELLOW = (255, 220, 0)
WARNING_DURATION = 45
BOOST_DURATION   = 120
LUCKY_DURATION   = 90
RAINBOW_COLORS   = [
    (255, 0, 0), (255, 127, 0), (255, 255, 0),
    (0, 200, 0), (0, 0, 255),   (148, 0, 211),
]


def _sy(y_720):
    """Scale y from 720-base to current SCREEN_HEIGHT."""
    return int(y_720 / 720 * SCREEN_HEIGHT)


# flash border surfaces (small rects instead of full-screen SRCALPHA)
def _make_hv(color, bsize):
    hs = pygame.Surface((SCREEN_WIDTH, bsize))
    vs = pygame.Surface((bsize, SCREEN_HEIGHT))
    hs.fill(color)
    vs.fill(color)
    return hs, vs


def _blit_border(surface, hs, vs, bsize, alpha):
    hs.set_alpha(alpha)
    vs.set_alpha(alpha)
    surface.blit(hs, (0, 0))
    surface.blit(hs, (0, SCREEN_HEIGHT - bsize))
    surface.blit(vs, (0, 0))
    surface.blit(vs, (SCREEN_WIDTH - bsize, 0))


_warn_hs = _warn_vs = None
_boost_hs = _boost_vs = None
_lucky_hs = _lucky_vs = None
_warn_text   = None
_boost_texts = None
_lucky_texts = None


class Player(pygame.sprite.Sprite):
    def __init__(self, pacman_img, pacman_close_img, red_pacman_img):
        super().__init__()
        self.pacman_img       = pacman_img
        self.pacman_close_img = pacman_close_img
        self.red_pacman_img   = red_pacman_img
        self.width  = _SP
        self.height = _SP
        self.rect = pygame.Rect(0, 0, _SP, _SP)
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom  = SCREEN_HEIGHT - 10
        self.speed = 8 if MOBILE else 10
        self.hurt_timer = 0
        self.eat_timer  = 0
        self.touch_x = None

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and self.rect.left  > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if self.touch_x is not None:
            new_cx = max(_SP // 2,
                         min(SCREEN_WIDTH - _SP // 2, self.touch_x))
            self.rect.centerx = new_cx
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.eat_timer  > 0: self.eat_timer  -= 1

    def draw(self, surface):
        if   self.hurt_timer > 0: img = self.red_pacman_img
        elif self.eat_timer  > 0: img = self.pacman_close_img
        else:                     img = self.pacman_img
        surface.blit(img, self.rect)


class Food(pygame.sprite.Sprite):
    def __init__(self, food_type, images, start_y=None):
        super().__init__()
        self.food_type = food_type
        self.width  = _SF
        self.height = _SF

        if food_type == "taco":
            self.image  = images["taco"].copy()
            self.points = 10
        elif food_type == "giant_taco":
            self.width  = _SFG
            self.height = _SFG
            self.image  = images["giant_taco"].copy()
            self.points = 50
        elif food_type == "milkshake":
            self.height = int(82 * _SF / 60)
            self.image  = images[random.choice(["milkshake", "oreo_milkshake"])].copy()
            self.points = 20
        elif food_type == "spider":
            self.image  = images["spider"].copy()
            self.points = 0
        else:
            self.image  = images["snake"].copy()
            self.points = 0

        self.rect   = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, SCREEN_WIDTH - self.width))
        self.rect.y = start_y if start_y is not None else random.randint(-100, -40)
        self.speed  = 2 if food_type == "giant_taco" else random.randint(2, 5)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def draw(self, surface):
        surface.blit(self.image, self.rect)


def draw_lives(surface, bad_count, heart_red, heart_gray):
    for i in range(5):
        img = heart_gray if i >= (5 - bad_count) else heart_red
        if MOBILE:
            # right-aligned, 5 hearts with gap
            x = SCREEN_WIDTH - (5 - i) * (_SH + 5)
        else:
            x = SCREEN_WIDTH - 260 + i * 46
        surface.blit(img, (x, 12))


def draw_boost_flash(surface, timer):
    alpha = int(180 * abs((timer % 20) - 10) / 10)
    _blit_border(surface, _boost_hs, _boost_vs, _BORDER_BOOST, alpha)
    txt = _boost_texts[(timer // 6) % 2]
    surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                        SCREEN_HEIGHT // 2 - 20))


def draw_lucky_flash(surface, timer):
    color_idx = (timer // 5) % len(RAINBOW_COLORS)
    r, g, b   = RAINBOW_COLORS[color_idx]
    alpha     = int(200 * abs((timer % 20) - 10) / 10)
    _lucky_hs.fill((r, g, b))
    _lucky_vs.fill((r, g, b))
    _blit_border(surface, _lucky_hs, _lucky_vs, _BORDER_LUCKY, alpha)
    txt = _lucky_texts[(timer // 3) % len(RAINBOW_COLORS)]
    surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                        SCREEN_HEIGHT // 2 - 20))


def draw_warning_flash(surface, timer):
    alpha = int(200 * (timer / WARNING_DURATION))
    _blit_border(surface, _warn_hs, _warn_vs, _BORDER_WARN, alpha)
    if (timer // 6) % 2 == 0:
        surface.blit(_warn_text, (SCREEN_WIDTH // 2 - _warn_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - 20))


def draw_start_screen(surface, font_large, font_mid, font_small, bg_image):
    surface.blit(bg_image, (0, 0))
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ov.fill((0, 0, 0))
    ov.set_alpha(120)
    surface.blit(ov, (0, 0))

    title = font_large.render("Tacoman Game", True, YELLOW)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, _sy(220)))

    btn_w, btn_h = int(SCREEN_WIDTH * 0.72), 55
    btn_x = SCREEN_WIDTH // 2 - btn_w // 2
    btn_y = _sy(360)
    pygame.draw.rect(surface, GREEN, (btn_x, btn_y, btn_w, btn_h), border_radius=10)
    pygame.draw.rect(surface, WHITE, (btn_x, btn_y, btn_w, btn_h), 2, border_radius=10)
    btn_text = font_mid.render("Start Game", True, WHITE)
    surface.blit(btn_text, (SCREEN_WIDTH // 2 - btn_text.get_width() // 2,
                             btn_y + (btn_h - btn_text.get_height()) // 2))

    hint = font_small.render("Reach 1000 points!", True, (200, 200, 200))
    surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, _sy(460)))
    touch = font_small.render("Watch out for spiders!", True, (160, 200, 160))
    surface.blit(touch, (SCREEN_WIDTH // 2 - touch.get_width() // 2, _sy(505)))

    return pygame.Rect(btn_x, btn_y, btn_w, btn_h)


RESTART_BTN_W = int(SCREEN_WIDTH * 0.72)
RESTART_BTN_RECT = pygame.Rect(
    SCREEN_WIDTH // 2 - RESTART_BTN_W // 2, _sy(500), RESTART_BTN_W, 55
)


def draw_restart_button(surface, font_mid):
    pygame.draw.rect(surface, GREEN, RESTART_BTN_RECT, border_radius=10)
    pygame.draw.rect(surface, WHITE, RESTART_BTN_RECT, 2, border_radius=10)
    txt = font_mid.render("Restart", True, WHITE)
    surface.blit(txt, (RESTART_BTN_RECT.centerx - txt.get_width()  // 2,
                        RESTART_BTN_RECT.centery - txt.get_height() // 2))


def draw_win_screen(surface, seconds, score, font_large, font_mid, font_small):
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ov.fill((0, 0, 0))
    ov.set_alpha(160)
    surface.blit(ov, (0, 0))
    for txt, y in [
        (font_large.render("YOU WIN!", True, YELLOW),             _sy(200)),
        (font_mid.render(f"Clear Time: {seconds}s", True, WHITE), _sy(300)),
        (font_mid.render(f"Final Score: {score}", True, WHITE),   _sy(370)),
    ]:
        surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
    draw_restart_button(surface, font_mid)
    q = font_small.render("ESC: Quit", True, (180, 180, 180))
    surface.blit(q, (SCREEN_WIDTH // 2 - q.get_width() // 2, _sy(590)))


def draw_lose_screen(surface, score, font_large, font_mid, font_small):
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ov.fill((0, 0, 0))
    ov.set_alpha(160)
    surface.blit(ov, (0, 0))
    for txt, y in [
        (font_large.render("GAME OVER", True, RED),          _sy(240)),
        (font_mid.render(f"Score: {score}", True, WHITE),    _sy(355)),
    ]:
        surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
    draw_restart_button(surface, font_mid)
    q = font_small.render("ESC: Quit", True, (180, 180, 180))
    surface.blit(q, (SCREEN_WIDTH // 2 - q.get_width() // 2, _sy(590)))


def _check_web_start():
    try:
        import platform
        return bool(platform.window.game_should_start)
    except Exception:
        return False


async def main():
    global _warn_hs, _warn_vs, _boost_hs, _boost_vs
    global _lucky_hs, _lucky_vs, _warn_text, _boost_texts, _lucky_texts

    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.init()
    pygame.mixer.set_num_channels(16)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Taco Eating Game")

    try:
        import platform as _plt
        _plt.window.loadingScreen_hide()
    except Exception:
        pass

    clock = pygame.time.Clock()

    font_large = pygame.font.Font(None, _FL)
    font_mid   = pygame.font.Font(None, _FM)
    font_small = pygame.font.Font(None, _FS)

    # init flash border surfaces
    _warn_hs,  _warn_vs  = _make_hv((220, 20, 60), _BORDER_WARN)
    _boost_hs, _boost_vs = _make_hv((255, 220, 0), _BORDER_BOOST)
    _lucky_hs, _lucky_vs = _make_hv((255, 0, 0),   _BORDER_LUCKY)

    # pre-render flash texts (avoid font.render every frame)
    _warn_text   = font_large.render("DANGER!", True, RED)
    _boost_texts = [font_large.render("BOOST!", True, YELLOW),
                    font_large.render("BOOST!", True, WHITE)]
    _lucky_texts = [font_large.render("LUCKY!", True, c) for c in RAINBOW_COLORS]

    await asyncio.sleep(0)

    pygame.mixer.music.load(f"{SOUND_PATH}/bg_sound.ogg")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

    eat_taco_sound  = pygame.mixer.Sound(f"{SOUND_PATH}/eat_taco_sound.ogg")
    eat_snake_sound = pygame.mixer.Sound(f"{SOUND_PATH}/eat_snake_sound.ogg")
    boost_sound     = pygame.mixer.Sound(f"{SOUND_PATH}/boost_sound.ogg")
    powerup_sound   = pygame.mixer.Sound(f"{SOUND_PATH}/power_up_sound.ogg")
    fail_sound      = pygame.mixer.Sound(f"{SOUND_PATH}/fail_sound.ogg")
    win_sound       = pygame.mixer.Sound(f"{SOUND_PATH}/win_sound.ogg")

    eat_taco_sound.set_volume(0.6)
    eat_snake_sound.set_volume(0.7)
    boost_sound.set_volume(0.7)
    powerup_sound.set_volume(0.8)

    _mh = int(82 * _SF / 60)  # milkshake height (proportional)

    bg_file  = "bg_mobile_img.png" if MOBILE else "bg_img.png"
    bg_image = pygame.image.load(f"{ASSET_PATH}/{bg_file}")
    bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    images = {
        "taco":          pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/taco.png"),            (_SF,  _SF)),
        "giant_taco":    pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/taco.png"),            (_SFG, _SFG)),
        "milkshake":     pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/milkshake.png"),       (_SF,  _mh)),
        "oreo_milkshake":pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/oreo_milkshake.png"), (_SF,  _mh)),
        "spider":        pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/spider.png"),          (_SF,  _SF)),
        "snake":         pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/snake.png"),           (_SF,  _SF)),
    }
    heart_red        = pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/red_heart.png"),         (_SH, _SH))
    heart_gray       = pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/gray_heart.png"),        (_SH, _SH))
    pacman_img       = pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/tx_pacman.png"),         (_SP, _SP))
    pacman_close_img = pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/tx_pacman_close.png"),   (_SP, _SP))
    red_pacman_img   = pygame.transform.scale(pygame.image.load(f"{ASSET_PATH}/tx_red_pacman.png"),     (_SP, _SP))

    score           = 0
    bad_count       = 0
    boost_active    = False
    boost_timer     = 0
    boost_spawn_count = 0
    warning_timer   = 0
    lucky_timer     = 0
    game_state      = "start"
    elapsed_seconds = 0
    spawn_timer     = 0
    spawn_interval  = 30
    start_ticks     = 0

    # score text cache (only re-render when score changes)
    score_surf  = font_large.render("Score: 0", True, BLACK)
    score_cache = 0

    player_group = pygame.sprite.Group()
    food_group   = pygame.sprite.Group()
    player = Player(pacman_img, pacman_close_img, red_pacman_img)
    player_group.add(player)

    btn_w = int(SCREEN_WIDTH * 0.72)
    start_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, _sy(360), btn_w, 55)

    DRAG_THRESHOLD = 10
    _touch_start_x = 0
    _is_dragging   = False

    def reset_game():
        nonlocal score, bad_count, boost_active, boost_timer, boost_spawn_count
        nonlocal warning_timer, lucky_timer, spawn_timer, score_surf, score_cache
        score, bad_count = 0, 0
        boost_active, boost_timer, boost_spawn_count = False, 0, 0
        warning_timer, lucky_timer, spawn_timer = 0, 0, 0
        food_group.empty()
        player.rect.centerx = SCREEN_WIDTH // 2
        player.hurt_timer = player.eat_timer = 0
        player.touch_x = None
        score_surf  = font_large.render("Score: 0", True, BLACK)
        score_cache = 0

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
                    game_state  = "playing"
                    start_ticks = pygame.time.get_ticks()
                    player.touch_x = None
                elif event.key == pygame.K_RETURN and game_state in ("win", "lose"):
                    powerup_sound.play()
                    reset_game()
                    game_state  = "playing"
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
                _is_dragging   = False
                if game_state == "start" and start_btn_rect.collidepoint(event.pos):
                    powerup_sound.play()
                    game_state  = "playing"
                    start_ticks = pygame.time.get_ticks()
                    player.touch_x = None
                elif game_state in ("win", "lose") and RESTART_BTN_RECT.collidepoint(event.pos):
                    powerup_sound.play()
                    reset_game()
                    game_state  = "playing"
                    start_ticks = pygame.time.get_ticks()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                player.touch_x = None
                _is_dragging   = False

            elif event.type == pygame.FINGERDOWN:
                fx = int(event.x * SCREEN_WIDTH)
                fy = int(event.y * SCREEN_HEIGHT)
                _touch_start_x = fx
                _is_dragging   = False
                if game_state == "start" and start_btn_rect.collidepoint(fx, fy):
                    powerup_sound.play()
                    game_state  = "playing"
                    start_ticks = pygame.time.get_ticks()
                    player.touch_x = None
                elif game_state in ("win", "lose") and RESTART_BTN_RECT.collidepoint(fx, fy):
                    powerup_sound.play()
                    reset_game()
                    game_state  = "playing"
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
                _is_dragging   = False

        if game_state == "start":
            if _check_web_start():
                powerup_sound.play()
                game_state  = "playing"
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
                food_type = random.choices(
                    ["taco", "spider", "snake", "milkshake", "giant_taco"],
                    weights=[6, 2, 2, 1, 1]
                )[0]
                food_group.add(Food(food_type, images))
                spawn_timer = 0

            if boost_active:
                boost_timer -= 1
                if boost_spawn_count > 0 and spawn_timer % 4 == 0:
                    for _ in range(2):
                        food_group.add(Food("taco", images, start_y=random.randint(-80, -20)))
                    boost_spawn_count -= 1
                if boost_timer <= 0:
                    boost_active = False
                    boost_spawn_count = 0

            if warning_timer > 0: warning_timer -= 1
            if lucky_timer   > 0: lucky_timer   -= 1

            player_group.update()
            food_group.update()

            player_hitbox = player.rect.inflate(-14, -14)
            for food in list(food_group):
                if player_hitbox.colliderect(food.rect.inflate(-14, -14)):
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
                        player.eat_timer  = 12
                        boost_active      = True
                        boost_timer       = BOOST_DURATION
                        boost_spawn_count = 8
                        boost_sound.play()
                    elif food.food_type in ("spider", "snake"):
                        bad_count        += 1
                        warning_timer     = WARNING_DURATION
                        player.hurt_timer = 60
                        eat_snake_sound.play()
                    food.kill()

            if score >= 1000:
                game_state      = "win"
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
            # re-render score only when value changes
            if score != score_cache:
                score_surf  = font_large.render(f"Score: {score}", True, BLACK)
                score_cache = score
            screen.blit(score_surf, (8, 10))
            draw_lives(screen, bad_count, heart_red, heart_gray)
            if warning_timer > 0: draw_warning_flash(screen, warning_timer)
            if lucky_timer   > 0: draw_lucky_flash(screen, lucky_timer)
            if boost_active:      draw_boost_flash(screen, boost_timer)

        elif game_state == "win":
            player.draw(screen)
            for food in food_group:
                food.draw(screen)
            draw_win_screen(screen, elapsed_seconds, score, font_large, font_mid, font_small)

        elif game_state == "lose":
            player.draw(screen)
            for food in food_group:
                food.draw(screen)
            draw_lose_screen(screen, score, font_large, font_mid, font_small)

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
