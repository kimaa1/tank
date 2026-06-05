"""
坦克大战 (Tank Battle) - Pygame 版本
经典 FC 坦克大战的 Python 复刻

运行方式:
    pip install pygame
    python tank_battle.py
"""

import pygame
import sys
import math
import random
from collections import namedtuple

# ==================== 初始化 ====================
pygame.init()
pygame.mixer.init()

# ==================== 常量 ====================
TILE = 32
COLS = 20
ROWS = 15
WIDTH = COLS * TILE      # 640
HEIGHT = ROWS * TILE     # 480
FPS = 60

# 方向
UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]

# 地图元素
EMPTY, BRICK, STEEL, WATER, TREE, BASE = 0, 1, 2, 3, 4, 5

# 颜色
BLACK       = (0, 0, 0)
DARK_GRAY   = (26, 26, 26)
WHITE       = (255, 255, 255)
YELLOW      = (255, 255, 0)
RED         = (255, 50, 50)
GREEN       = (70, 170, 70)
ORANGE      = (255, 140, 0)
BRICK_COLOR = (181, 101, 29)
STEEL_COLOR = (136, 136, 136)
WATER_COLOR = (34, 85, 170)

# 坦克参数
TANK_SIZE = 28
HALF_TANK = TANK_SIZE // 2
PLAYER_SPEED = 2.5
ENEMY_SPEED = 1.2
BULLET_SPEED = 6
PLAYER_SHOOT_DELAY = 20
ENEMY_SHOOT_DELAY = 60

# ==================== 屏幕 ====================
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("坦克大战 - Tank Battle")
clock = pygame.time.Clock()
font_small = pygame.font.SysFont("simhei", 11)
font_medium = pygame.font.SysFont("simhei", 20)
font_large = pygame.font.SysFont("simhei", 36)

# ==================== 音效生成 ====================
def generate_sound(freq, duration, vol=0.1):
    """生成简单音效"""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = bytearray(n_samples * 2)  # 16-bit mono
    for i in range(n_samples):
        t = i / sample_rate
        # 方波 + 衰减
        val = (1 if (t * freq) % 1 < 0.5 else -1)
        envelope = max(0, 1 - i / n_samples)
        val = int(val * envelope * vol * 32767)
        buf[i * 2] = val & 0xFF
        buf[i * 2 + 1] = (val >> 8) & 0xFF
    return pygame.mixer.Sound(buffer(bytes(buf)))

# 预生成音效
try:
    sound_shoot  = generate_sound(800, 0.08, 0.08)
    sound_hit    = generate_sound(150, 0.15, 0.12)
    sound_explode = generate_sound(60, 0.3, 0.15)
    sound_power  = generate_sound(1200, 0.1, 0.08)
    sound_gameover = generate_sound(200, 0.5, 0.2)
except:
    # 如果音频不可用，创建静音
    sound_shoot = sound_hit = sound_explode = sound_power = sound_gameover = None

def play_sound(sound):
    if sound:
        try:
            sound.play()
        except:
            pass

# ==================== 地图 ====================
MAPS = [
    # 关卡 1
    [
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,
        0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,
        0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,
        0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,
        0,0,0,0,0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0,
        0,0,0,0,0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0,
        2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        2,2,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,1,1,
        0,0,1,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,1,1,
        0,0,1,1,0,0,0,0,1,0,0,1,0,0,1,1,0,0,0,0,
        0,0,1,1,0,0,1,1,1,0,0,1,1,1,1,1,0,0,0,0,
        0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,1,1,0,0,0,5,5,0,0,0,0,0,0,0,
    ],
    # 关卡 2
    [
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        1,1,0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0,1,1,
        1,1,0,0,1,1,0,0,2,2,2,2,0,0,1,1,0,0,1,1,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,
        0,0,2,2,0,0,1,1,0,0,0,0,1,1,0,0,2,2,0,0,
        0,0,2,2,0,0,1,1,0,0,0,0,1,1,0,0,2,2,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,1,0,0,1,1,0,0,1,0,0,0,0,0,0,
        0,0,1,1,0,0,0,0,1,0,0,1,0,0,0,0,1,1,0,0,
        0,0,1,1,0,0,0,0,1,0,0,1,0,0,0,0,1,1,0,0,
        0,0,1,1,0,0,1,1,1,0,0,1,1,1,0,0,1,1,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,5,5,0,0,0,0,0,0,0,0,
    ],
    # 关卡 3
    [
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
        1,1,1,1,0,0,2,2,0,0,0,0,2,2,0,0,1,1,1,1,
        0,0,0,0,0,0,2,2,0,0,0,0,2,2,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,
        0,0,1,1,0,0,0,0,1,1,1,1,0,0,0,0,1,1,0,0,
        0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,
        2,2,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,2,2,
        2,2,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,2,2,
        0,0,1,1,0,0,0,0,1,1,1,1,0,0,0,0,1,1,0,0,
        0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,5,5,0,0,0,0,0,0,0,0,
    ],
]

# ==================== 类定义 ====================

class Tank:
    def __init__(self, x, y, direction, speed, color, is_player):
        self.x = float(x)
        self.y = float(y)
        self.direction = direction
        self.speed = speed
        self.color = color
        self.is_player = is_player
        self.alive = True
        self.bullet = None
        self.shoot_cooldown = 0
        self.shoot_delay = PLAYER_SHOOT_DELAY if is_player else ENEMY_SHOOT_DELAY
        self.frozen_timer = 90 if is_player else 60  # 出生保护
        self.flash_timer = 0
        self.half = TANK_SIZE // 2
        self.move_progress = 0

    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.half), int(self.y - self.half),
            TANK_SIZE, TANK_SIZE
        )

    def collides_with(self, other_tank):
        return self.get_rect().colliderect(other_tank.get_rect())

    def collides_with_map(self, game_map):
        r = self.get_rect()
        # 检测四角和四边中点
        pts = [
            (r.left + 2, r.top + 2), (r.right - 2, r.top + 2),
            (r.left + 2, r.bottom - 2), (r.right - 2, r.bottom - 2),
            (r.centerx, r.top + 2), (r.centerx, r.bottom - 2),
            (r.left + 2, r.centery), (r.right - 2, r.centery),
        ]
        for px, py in pts:
            if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT:
                return True
            col, row = int(px // TILE), int(py // TILE)
            if 0 <= col < COLS and 0 <= row < ROWS:
                tile = game_map[row * COLS + col]
                if tile in (BRICK, STEEL, WATER, BASE):
                    return True
        return False

    def shoot(self):
        if self.bullet is not None or self.shoot_cooldown > 0:
            return None
        self.shoot_cooldown = self.shoot_delay
        bx = self.x + DX[self.direction] * (self.half + 2)
        by = self.y + DY[self.direction] * (self.half + 2)
        self.bullet = Bullet(bx, by, self.direction, self.is_player, self)
        play_sound(sound_shoot)
        return self.bullet

    def update(self, game_map, tanks):
        if not self.alive:
            return
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            self.flash_timer = (self.flash_timer + 1) % 8
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.bullet and not self.bullet.alive:
            self.bullet = None

    def draw(self, surface):
        if not self.alive:
            return
        if self.frozen_timer > 0 and self.flash_timer < 4:
            return

        # 保存并旋转坐标系
        cx, cy = int(self.x), int(self.y)
        surf = pygame.Surface((TANK_SIZE + 4, TANK_SIZE + 4), pygame.SRCALPHA)
        hw, hh = self.half + 2, self.half + 2  # center offset

        # 履带
        pygame.draw.rect(surf, (34, 34, 34), (hw - self.half, hh - self.half,
                          int(self.half * 0.3), self.half * 2))
        pygame.draw.rect(surf, (34, 34, 34), (hw + int(self.half * 0.7), hh - self.half,
                          int(self.half * 0.3), self.half * 2))
        # 履带纹理
        for i in range(-self.half + 4, self.half, 6):
            pygame.draw.rect(surf, (68, 68, 68), (hw - self.half + 1, hh + i,
                              int(self.half * 0.3) - 2, 3))
            pygame.draw.rect(surf, (68, 68, 68), (hw + int(self.half * 0.7) + 1, hh + i,
                              int(self.half * 0.3) - 2, 3))

        # 车身
        body_color = self.color
        bx = hw - int(self.half * 0.55)
        bw = int(self.half * 1.1)
        pygame.draw.rect(surf, body_color, (bx, hh - int(self.half * 0.85), bw, int(self.half * 1.7)))
        # 车身细节
        detail_color = (100, 200, 100) if self.is_player else (170, 60, 60)
        pygame.draw.rect(surf, detail_color, (bx + 3, hh - int(self.half * 0.65),
                          bw - 6, int(self.half * 0.5)))

        # 炮塔
        turret_color = (255, 255, 0) if self.is_player else (210, 210, 210)
        pygame.draw.circle(surf, turret_color, (hw, hh), int(self.half * 0.35))

        # 炮管
        pygame.draw.rect(surf, turret_color, (hw - 2, hh - self.half - 2, 4, int(self.half * 0.7) + 2))
        pygame.draw.rect(surf, WHITE, (hw - 1, hh - self.half - 4, 2, 4))

        # 旋转 surface（pygame 旋转: 上=0度, 顺时针增加。我们的方向: 上=0, 右=1, 下=2, 左=3）
        angle = -90 * self.direction  # pygame 旋转是逆时针的, 所以要取负
        rotated = pygame.transform.rotate(surf, angle)
        new_rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, new_rect)

        # 无敌光圈
        if self.frozen_timer > 0 and self.flash_timer >= 4:
            pygame.draw.circle(surface, (255, 255, 255, 100), (cx, cy), self.half + 4, 2)

        # 子弹
        if self.bullet and self.bullet.alive:
            self.bullet.draw(surface)


class Bullet:
    def __init__(self, x, y, direction, is_player_bullet, owner):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = BULLET_SPEED
        self.alive = True
        self.is_player_bullet = is_player_bullet
        self.owner = owner
        self.size = 4

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size,
                           self.size * 2, self.size * 2)

    def update(self, game_map, tanks, game):
        if not self.alive:
            return
        self.x += DX[self.direction] * self.speed
        self.y += DY[self.direction] * self.speed

        # 边界
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.die()
            return

        # 地图碰撞
        col, row = int(self.x // TILE), int(self.y // TILE)
        if 0 <= col < COLS and 0 <= row < ROWS:
            tile = game_map[row * COLS + col]
            if tile == BRICK:
                game_map[row * COLS + col] = EMPTY
                game.spawn_explosion(col * TILE + TILE // 2, row * TILE + TILE // 2, False)
                play_sound(sound_hit)
                self.die()
                return
            elif tile == STEEL:
                game.spawn_explosion(self.x, self.y, True)
                play_sound(sound_hit)
                self.die()
                return
            elif tile == BASE:
                game_map[row * COLS + col] = EMPTY
                if row + 1 < ROWS:
                    game_map[(row + 1) * COLS + col] = EMPTY
                self.die()
                game.base_destroyed()
                return

        # 坦克碰撞
        for tank in tanks:
            if not tank.alive or tank is self.owner:
                continue
            if tank.frozen_timer > 0:
                continue
            if self.is_player_bullet == tank.is_player:
                continue
            if self.get_rect().colliderect(tank.get_rect()):
                tank.alive = False
                game.spawn_explosion(tank.x, tank.y, False)
                play_sound(sound_explode)
                self.die()
                if tank.is_player:
                    game.player_died()
                else:
                    game.enemy_killed(tank)
                return

        # 子弹互碰
        for tank in tanks:
            if not tank.alive or tank is self.owner:
                continue
            if tank.bullet is None or not tank.bullet.alive or tank.bullet is self:
                continue
            if self.get_rect().colliderect(tank.bullet.get_rect()):
                game.spawn_explosion(self.x, self.y, True)
                self.die()
                tank.bullet.die()
                tank.bullet = None
                return

    def die(self):
        self.alive = False
        if self.owner:
            self.owner.bullet = None

    def draw(self, surface):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        # 子弹球体
        color = (255, 255, 200) if self.is_player_bullet else (255, 170, 150)
        pygame.draw.circle(surface, color, (cx, cy), self.size)
        # 拖尾
        tx = int(cx - DX[self.direction] * 3)
        ty = int(cy - DY[self.direction] * 3)
        tail_color = (255, 255, 150, 150) if self.is_player_bullet else (255, 180, 120, 120)
        pygame.draw.circle(surface, tail_color[:3], (tx, ty), max(1, self.size - 1))


class Explosion:
    def __init__(self, x, y, small):
        self.x = x
        self.y = y
        self.life = 8 if small else 18
        self.max_life = self.life
        count = 6 if small else 14
        self.particles = []
        for i in range(count):
            angle = (math.pi * 2 * i / count) + (random.random() - 0.5) * 0.5
            spd = 1 + random.random() * 2.5
            self.particles.append({
                'x': 0.0, 'y': 0.0,
                'vx': math.cos(angle) * spd,
                'vy': math.sin(angle) * spd,
                'size': (1.5 + random.random() * 2) if small else (2 + random.random() * 4),
                'color': (255, 140, 0) if random.random() < 0.5 else (255, 200, 0),
            })

    def update(self):
        self.life -= 1
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.94
            p['vy'] *= 0.94
        return self.life > 0

    def draw(self, surface):
        alpha = self.life / self.max_life
        for p in self.particles:
            px = int(self.x + p['x'])
            py = int(self.y + p['y'])
            size = int(p['size'] * alpha)
            if size < 1:
                continue
            # 使用带 alpha 的 surface
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = (*p['color'], int(255 * alpha))
            pygame.draw.circle(s, color, (size, size), size)
            surface.blit(s, (px - size, py - size))


class PowerUp:
    ICONS = {
        'star':   '★',
        'shield': '🛡',
        'freeze': '❄',
        'bomb':   '💣',
        'life':   '❤',
    }

    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype
        self.alive = True
        self.timer = 600  # 10 秒后消失
        self.flash = 0

    def get_rect(self):
        return pygame.Rect(self.x - 14, self.y - 14, 28, 28)

    def update(self):
        self.timer -= 1
        self.flash = (self.flash + 1) % 30
        if self.timer <= 0:
            self.alive = False
        return self.alive

    def draw(self, surface):
        if not self.alive:
            return
        # 最后 3 秒闪烁
        if self.timer < 180 and (self.flash // 15) % 2 == 0:
            return
        rect = self.get_rect()
        pygame.draw.rect(surface, (50, 50, 50), rect)
        pygame.draw.rect(surface, (130, 130, 130), rect, 2)

        # 图标 - 用文字表示
        icon_text = self.ICONS.get(self.type, '?')
        txt = font_medium.render(icon_text, True, WHITE)
        txt_rect = txt.get_rect(center=(self.x, self.y + 2))
        surface.blit(txt, txt_rect)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.level = 0
        self.lives = 3
        self.score = 0
        self.total_enemies = 10
        self.killed_enemies = 0
        self.active_enemies = 0
        self.max_active_enemies = 4
        self.spawn_timer = 60
        self.spawn_delay = 120
        self.player = None
        self.enemies = []
        self.explosions = []
        self.power_ups = []
        self.game_map = []
        self.paused = False
        self.game_over = False
        self.game_win = False
        self.base_alive = True
        self.message = ''
        self.message_timer = 0
        self.enemy_spawn_points = [
            (0 * TILE + TILE // 2, TILE // 2),
            (9 * TILE + TILE // 2, TILE // 2),
            (19 * TILE + TILE // 2, TILE // 2),
        ]
        self.init_level(0)

    def init_level(self, level):
        self.level = level
        self.game_map = MAPS[level % len(MAPS)][:]
        self.killed_enemies = 0
        self.active_enemies = 0
        self.spawn_timer = 60
        self.enemies = []
        self.explosions = []
        self.power_ups = []
        self.paused = False
        self.game_over = False
        self.game_win = False
        self.base_alive = True

        # 创建玩家
        px = 9 * TILE + TILE // 2
        py = 14 * TILE + TILE // 2
        self.player = Tank(px, py, UP, PLAYER_SPEED, (70, 170, 70), True)

    def spawn_enemy(self):
        if self.killed_enemies + self.active_enemies >= self.total_enemies:
            return
        if self.active_enemies >= self.max_active_enemies:
            return

        sx, sy = random.choice(self.enemy_spawn_points)
        temp = Tank(sx, sy, DOWN, ENEMY_SPEED, (200, 60, 60), False)
        # 碰撞检测
        blocked = temp.collides_with_map(self.game_map)
        for e in self.enemies:
            if e.alive and temp.collides_with(e):
                blocked = True
                break
        if self.player and self.player.alive and temp.collides_with(self.player):
            blocked = True
        if blocked:
            return

        colors = [(230, 70, 70), (220, 130, 60), (200, 100, 200),
                  (130, 170, 255), (250, 160, 60)]
        enemy = Tank(sx, sy, DOWN, ENEMY_SPEED, random.choice(colors), False)
        enemy.frozen_timer = 50
        self.enemies.append(enemy)
        self.active_enemies += 1

    def enemy_ai(self, enemy):
        if not enemy.alive or enemy.frozen_timer > 0:
            return

        if random.random() < 0.02:
            enemy.direction = random.choice([UP, DOWN, LEFT, RIGHT])

        # 朝玩家射击
        if random.random() < 0.03 and self.player and self.player.alive:
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            enemy.direction = RIGHT if abs(dx) > abs(dy) and dx > 0 else \
                              LEFT if abs(dx) > abs(dy) else \
                              DOWN if dy > 0 else UP
            enemy.shoot()
        elif random.random() < 0.015:
            enemy.shoot()

        # 移动
        nx = enemy.x + DX[enemy.direction] * enemy.speed
        ny = enemy.y + DY[enemy.direction] * enemy.speed
        ox, oy = enemy.x, enemy.y
        enemy.x, enemy.y = nx, ny

        collision = enemy.collides_with_map(self.game_map)
        if not collision:
            all_tanks = [self.player] + self.enemies if self.player else self.enemies
            for t in all_tanks:
                if t and t.alive and t is not enemy and enemy.collides_with(t):
                    collision = True
                    break

        if collision:
            enemy.x, enemy.y = ox, oy
            dirs = [d for d in [UP, DOWN, LEFT, RIGHT] if d != enemy.direction]
            enemy.direction = random.choice(dirs)

    def player_died(self):
        self.lives -= 1
        self.player = None
        if self.lives <= 0:
            self.show_message("游戏结束!", 180)
            play_sound(sound_gameover)
            pygame.time.set_timer(pygame.USEREVENT + 1, 1800, True)
        else:
            self.show_message(f"剩余生命: {self.lives}", 120)
            pygame.time.set_timer(pygame.USEREVENT + 2, 1000, True)

    def respawn_player(self):
        if self.game_over:
            return
        px = 9 * TILE + TILE // 2
        py = 14 * TILE + TILE // 2
        self.player = Tank(px, py, UP, PLAYER_SPEED, (70, 170, 70), True)

    def enemy_killed(self, enemy):
        self.active_enemies -= 1
        self.killed_enemies += 1
        self.score += 100

        # 随机掉落道具
        if random.random() < 0.25:
            types = ['star', 'star', 'shield', 'freeze', 'bomb', 'life']
            self.power_ups.append(PowerUp(enemy.x, enemy.y, random.choice(types)))

        if self.killed_enemies >= self.total_enemies:
            self.show_message("关卡完成!", 180)
            pygame.time.set_timer(pygame.USEREVENT + 3, 2000, True)

    def base_destroyed(self):
        if not self.base_alive:
            return
        self.base_alive = False
        self.show_message("基地被摧毁!", 180)
        play_sound(sound_gameover)
        pygame.time.set_timer(pygame.USEREVENT + 1, 1800, True)

    def show_message(self, msg, duration):
        self.message = msg
        self.message_timer = duration

    def next_level(self):
        self.level += 1
        if self.level >= len(MAPS) * 3:
            self.total_enemies = 10 + (self.level // len(MAPS)) * 3
        self.score += 500
        self.init_level(self.level)
        self.show_message(f"第 {self.level + 1} 关", 120)

    def end_game(self, won):
        self.game_over = True
        self.game_win = won
        self.player = None
        self.enemies = []

    def spawn_explosion(self, x, y, small):
        self.explosions.append(Explosion(x, y, small))

    def handle_input(self):
        if not self.player or not self.player.alive:
            return

        keys = pygame.key.get_pressed()
        p = self.player
        move_dir = None

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_dir = UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_dir = DOWN
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir = LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir = RIGHT

        if move_dir is not None:
            p.direction = move_dir
            nx = p.x + DX[p.direction] * p.speed
            ny = p.y + DY[p.direction] * p.speed
            ox, oy = p.x, p.y
            p.x, p.y = nx, ny

            collision = p.collides_with_map(self.game_map)
            if not collision:
                for e in self.enemies:
                    if e.alive and p.collides_with(e):
                        collision = True
                        break
            if collision:
                p.x, p.y = ox, oy

        if keys[pygame.K_SPACE] or keys[pygame.K_j]:
            p.shoot()

    def handle_power_ups(self):
        if not self.player or not self.player.alive:
            return
        for pu in self.power_ups:
            if not pu.alive:
                continue
            if pu.get_rect().colliderect(self.player.get_rect()):
                pu.alive = False
                play_sound(sound_power)
                if pu.type == 'star':
                    self.player.shoot_delay = max(5, self.player.shoot_delay - 5)
                    self.show_message("射速提升!", 60)
                elif pu.type == 'shield':
                    self.player.frozen_timer = 300
                    self.show_message("无敌护盾!", 60)
                elif pu.type == 'freeze':
                    for e in self.enemies:
                        if e.alive:
                            e.frozen_timer = max(e.frozen_timer, 180)
                    self.show_message("冻结敌人!", 60)
                elif pu.type == 'bomb':
                    for e in self.enemies:
                        if e.alive:
                            e.alive = False
                            self.spawn_explosion(e.x, e.y, False)
                            self.active_enemies -= 1
                            self.killed_enemies += 1
                            self.score += 50
                    self.enemies = []
                    self.show_message("全屏炸弹!", 60)
                elif pu.type == 'life':
                    self.lives += 1
                    self.show_message("生命+1!", 60)

    def update(self):
        if self.paused or self.game_over:
            return

        # 玩家输入
        self.handle_input()

        # 敌人生成
        if self.spawn_timer > 0:
            self.spawn_timer -= 1
        else:
            self.spawn_enemy()
            self.spawn_timer = self.spawn_delay + random.randint(0, 60)

        # 所有坦克
        all_tanks = [self.player] + self.enemies if self.player else list(self.enemies)

        # 更新坦克
        if self.player:
            self.player.update(self.game_map, all_tanks)
        for e in self.enemies:
            if e.alive:
                self.enemy_ai(e)
                e.update(self.game_map, all_tanks)

        # 更新子弹
        for tank in all_tanks:
            if tank and tank.bullet and tank.bullet.alive:
                tank.bullet.update(self.game_map, all_tanks, self)

        # 更新爆炸
        self.explosions = [exp for exp in self.explosions if exp.update()]

        # 更新道具
        self.power_ups = [pu for pu in self.power_ups if pu.update()]
        self.handle_power_ups()

        # 清理死亡敌人
        self.enemies = [e for e in self.enemies if e.alive]

        # 消息计时器
        if self.message_timer > 0:
            self.message_timer -= 1

        # 随机掉落道具
        if len(self.power_ups) == 0 and random.random() < 0.001:
            px = random.randint(60, WIDTH - 60)
            py = random.randint(60, HEIGHT - 60)
            col, row = int(px // TILE), int(py // TILE)
            if 0 <= col < COLS and 0 <= row < ROWS and self.game_map[row * COLS + col] == EMPTY:
                types = ['star', 'shield', 'freeze', 'life']
                self.power_ups.append(PowerUp(px, py, random.choice(types)))

    def draw(self, surface):
        # 背景
        surface.fill(DARK_GRAY)

        # 绘制地图
        for row in range(ROWS):
            for col in range(COLS):
                tile = self.game_map[row * COLS + col]
                x, y = col * TILE, row * TILE

                if tile == BRICK:
                    pygame.draw.rect(surface, BRICK_COLOR, (x, y, TILE, TILE))
                    # 砖块纹理
                    bh = TILE // 4
                    for r in range(4):
                        by = y + r * bh
                        if r in (1, 3):
                            pygame.draw.rect(surface, (201, 120, 58), (x, by, TILE // 2, bh))
                            pygame.draw.rect(surface, (201, 120, 58), (x + TILE // 2, by, TILE // 2, bh))
                        else:
                            pygame.draw.rect(surface, (201, 120, 58), (x, by, TILE // 2 - 2, bh))
                            pygame.draw.rect(surface, (201, 120, 58), (x + TILE // 2 + 2, by, TILE // 2 - 2, bh))
                    pygame.draw.rect(surface, (139, 69, 19), (x, y, TILE, TILE), 1)

                elif tile == STEEL:
                    pygame.draw.rect(surface, STEEL_COLOR, (x, y, TILE, TILE))
                    pygame.draw.rect(surface, (170, 170, 170), (x + 2, y + 2, TILE - 4, TILE - 4))
                    pygame.draw.rect(surface, (153, 153, 153), (x + 4, y + 4, TILE - 8, TILE - 8))
                    pygame.draw.rect(surface, (102, 102, 102), (x, y, TILE, TILE), 1)

                elif tile == WATER:
                    pygame.draw.rect(surface, WATER_COLOR, (x, y, TILE, TILE))
                    wave_offset = (pygame.time.get_ticks() // 200 + col + row) % (TILE * 2)
                    for wx in range(0, TILE, 8):
                        wy = int((wave_offset + wx * 0.5) % 8)
                        pygame.draw.rect(surface, (51, 102, 204), (x + wx, y + wy, 6, 2))

                elif tile == TREE:
                    pygame.draw.rect(surface, (45, 90, 30), (x, y, TILE, TILE))
                    pygame.draw.circle(surface, (58, 122, 38), (x + TILE // 2, y + TILE // 2), TILE // 2 - 2)
                    pygame.draw.circle(surface, (74, 154, 50), (x + TILE // 3, y + TILE // 3), TILE // 3)
                    pygame.draw.circle(surface, (74, 154, 50), (x + 2 * TILE // 3, y + TILE // 2), TILE // 4)

                elif tile == BASE:
                    pygame.draw.rect(surface, (50, 50, 50), (x, y, TILE, TILE * 2))
                    cx, cy = x + TILE // 2, y + TILE
                    # 鹰标
                    eagle_pts = [
                        (cx, cy - TILE + 4),
                        (cx + TILE // 3, cy),
                        (cx + TILE // 6, cy),
                        (cx + TILE // 6, cy + TILE - 4),
                        (cx - TILE // 6, cy + TILE - 4),
                        (cx - TILE // 6, cy),
                        (cx - TILE // 3, cy),
                    ]
                    pygame.draw.polygon(surface, (255, 204, 0), eagle_pts)
                    base_txt = font_small.render("BASE", True, WHITE)
                    surface.blit(base_txt, (cx - base_txt.get_width() // 2, cy + TILE // 2 + 2))

        # 道具
        for pu in self.power_ups:
            pu.draw(surface)

        # 坦克（先画敌人再画玩家，玩家在最上面）
        for e in self.enemies:
            if e.alive:
                e.draw(surface)
        if self.player and self.player.alive:
            self.player.draw(surface)

        # 树丛遮罩（画在坦克上方）
        for row in range(ROWS):
            for col in range(COLS):
                if self.game_map[row * COLS + col] == TREE:
                    x, y = col * TILE, row * TILE
                    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                    s.fill((30, 90, 20, 140))
                    surface.blit(s, (x, y))
                    pygame.draw.circle(surface, (45, 120, 30, 140), (x + TILE // 2, y + TILE // 2), TILE // 2 - 1)

        # 爆炸
        for exp in self.explosions:
            exp.draw(surface)

        # UI
        ui_surf = pygame.Surface((WIDTH, 18), pygame.SRCALPHA)
        ui_surf.fill((0, 0, 0, 180))
        surface.blit(ui_surf, (0, 0))

        # 文字
        level_txt = font_small.render(f"关: {self.level + 1}", True, WHITE)
        score_txt = font_small.render(f"得分: {self.score}", True, WHITE)
        lives_txt = font_small.render(f"生命: {'❤' * self.lives}", True, WHITE)
        remain_txt = font_small.render(f"剩余敌人: {self.total_enemies - self.killed_enemies}", True, WHITE)

        surface.blit(level_txt, (8, 2))
        surface.blit(score_txt, (90, 2))
        surface.blit(lives_txt, (210, 2))
        surface.blit(remain_txt, (WIDTH - remain_txt.get_width() - 8, 2))

        # 暂停
        if self.paused:
            pause_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pause_surf.fill((0, 0, 0, 150))
            surface.blit(pause_surf, (0, 0))
            pause_txt = font_large.render("暂 停", True, WHITE)
            hint_txt = font_medium.render("按 P 继续", True, WHITE)
            surface.blit(pause_txt, pause_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            surface.blit(hint_txt, hint_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35)))

        # 消息
        if self.message_timer > 0:
            alpha = min(255, int((self.message_timer / 30) * 255))
            msg_txt = font_medium.render(self.message, True, (255, 255, 255))
            msg_surf = pygame.Surface(msg_txt.get_size(), pygame.SRCALPHA)
            msg_surf.blit(msg_txt, (0, 0))
            msg_surf.set_alpha(alpha)
            surface.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            surface.blit(overlay, (0, 0))

            if self.game_win:
                title = font_large.render("胜 利 !", True, (255, 200, 0))
            else:
                title = font_large.render("游 戏 结 束", True, RED)
            surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

            score_txt = font_medium.render(f"得分: {self.score}  关卡: {self.level + 1}", True, WHITE)
            surface.blit(score_txt, score_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

            restart_txt = font_medium.render("按 R 重新开始  按 Q 退出", True, (200, 200, 200))
            surface.blit(restart_txt, restart_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p and not self.game_over:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()
                    elif event.key == pygame.K_q and self.game_over:
                        running = False

                elif event.type == pygame.USEREVENT + 1:  # 游戏结束
                    self.end_game(False)
                elif event.type == pygame.USEREVENT + 2:  # 玩家复活
                    self.respawn_player()
                elif event.type == pygame.USEREVENT + 3:  # 下一关
                    if not self.game_over:
                        self.next_level()

            self.update()
            self.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 主程序 ====================
if __name__ == '__main__':
    game = Game()
    game.run()
