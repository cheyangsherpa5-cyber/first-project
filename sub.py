import pygame
import random
import sys

# main.py
# A playable Snake game with selectable snake "types" and progressive difficulty/levels.
# Requires: pygame (pip install pygame)


# Config
CELL_SIZE = 20
GRID_WIDTH = 28
GRID_HEIGHT = 24
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT + 40  # room for HUD
FONT_SIZE = 20

BASE_MOVE_INTERVAL = 150  # milliseconds between moves at level 1 for classic snake

# Snake type definitions
SNAKE_TYPES = {
    "Classic": {
        "color": (0, 200, 0),
        "speed_mult": 1.0,
        "growth": 1,
        "pass_walls": False,
        "thickness": 1
    },
    "Speed": {
        "color": (255, 165, 0),
        "speed_mult": 1.5,
        "growth": 1,
        "pass_walls": False,
        "thickness": 1
    },
    "Tank": {
        "color": (20, 120, 255),
        "speed_mult": 0.85,
        "growth": 2,
        "pass_walls": False,
        "thickness": 2
    },
    "Ghost": {
        "color": (180, 180, 180),
        "speed_mult": 1.0,
        "growth": 1,
        "pass_walls": True,  # wraps around edges, can't die by walls
        "thickness": 1
    },
    "Slim": {
        "color": (200, 0, 200),
        "speed_mult": 1.25,
        "growth": 1,
        "pass_walls": False,
        "thickness": 1
    }
}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", FONT_SIZE)


# helpers
def draw_text(surface, text, x, y, color=(255, 255, 255)):
    txt = font.render(text, True, color)
    surface.blit(txt, (x, y))


def random_cell(exclude):
    while True:
        pos = (random.randrange(GRID_WIDTH), random.randrange(GRID_HEIGHT))
        if pos not in exclude:
            return pos


class Snake:
    def __init__(self, snake_type_name):
        self.type_name = snake_type_name
        t = SNAKE_TYPES[snake_type_name]
        self.color = t["color"]
        self.speed_mult = t["speed_mult"]
        self.growth_amount = t["growth"]
        self.pass_walls = t["pass_walls"]
        self.thickness = t["thickness"]

        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.segments = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.dir = (1, 0)
        self.next_dir = (1, 0)
        self.grow_pending = 0

    def set_direction(self, d):
        # prevent reversing directly
        if (d[0] == -self.dir[0] and d[1] == -self.dir[1]) and len(self.segments) > 1:
            return
        self.next_dir = d

    def update(self, obstacles):
        self.dir = self.next_dir
        head = self.segments[0]
        new_head = (head[0] + self.dir[0], head[1] + self.dir[1])

        if self.pass_walls:
            new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)

        self.segments.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.segments.pop()

        # collision checks will be handled externally (self collision and obstacle)
        return new_head

    def grow(self, amount=None):
        if amount is None:
            amount = self.growth_amount
        self.grow_pending += amount

    def draw(self, surface):
        for i, seg in enumerate(self.segments):
            x, y = seg
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            # slight visual for head
            if i == 0:
                head_color = tuple(min(255, c + 40) for c in self.color)
                pygame.draw.rect(surface, head_color, rect)
            else:
                pygame.draw.rect(surface, self.color, rect)

    def collides_with_self(self):
        head = self.segments[0]
        return head in self.segments[1:]


class Apple:
    def __init__(self, pos, kind="normal"):
        self.pos = pos
        self.kind = kind
        # kind could affect score/growth; we'll keep normal and golden for variety

    def draw(self, surface):
        x, y = self.pos
        center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
        if self.kind == "normal":
            color = (255, 50, 50)
            radius = CELL_SIZE // 2 - 2
        else:  # golden
            color = (255, 215, 0)
            radius = CELL_SIZE // 2 - 2
        pygame.draw.circle(surface, color, center, radius)


class Game:
    def __init__(self, snake_type):
        self.snake = Snake(snake_type)
        self.level = 1
        self.score = 0
        self.apples_eaten = 0
        self.obstacles = set()
        self.generate_obstacles()
        self.spawn_apple()
        self.last_move_time = pygame.time.get_ticks()
        self.move_interval = self.compute_move_interval()
        self.game_over = False
        self.paused = False

    def compute_move_interval(self):
        # Decrease interval as level goes up and according to snake speed
        level_factor = 1.0 + (self.level - 1) * 0.08  # 8% faster per level
        interval = BASE_MOVE_INTERVAL / (self.snake.speed_mult * level_factor)
        # clamp
        return max(30, int(interval))

    def generate_obstacles(self):
        # more obstacles with higher levels
        self.obstacles.clear()
        num = min(1 + (self.level - 1) // 2, 10)
        # keep a central free area
        safe = set()
        sx = GRID_WIDTH // 2
        sy = GRID_HEIGHT // 2
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                safe.add((sx + dx, sy + dy))
        # place obstacles not overlapping snake
        for _ in range(num):
            w = random.randint(1, 4)
            h = random.randint(1, 3)
            x = random.randint(0, GRID_WIDTH - w - 1)
            y = random.randint(0, GRID_HEIGHT - h - 1)
            block = [(x + ix, y + iy) for ix in range(w) for iy in range(h)]
            if any(p in safe or p in self.obstacles for p in block):
                continue
            self.obstacles.update(block)

    def spawn_apple(self):
        exclude = set(self.snake.segments) | self.obstacles
        # occasionally spawn golden apple
        kind = "golden" if random.random() < min(0.05 + 0.01 * self.level, 0.15) else "normal"
        pos = random_cell(exclude)
        self.apple = Apple(pos, kind=kind)

    def update(self):
        if self.game_over or self.paused:
            return

        now = pygame.time.get_ticks()
        if now - self.last_move_time >= self.move_interval:
            self.last_move_time = now
            new_head = self.snake.update(self.obstacles)

            # wall collision
            hx, hy = new_head
            if not self.snake.pass_walls:
                if hx < 0 or hx >= GRID_WIDTH or hy < 0 or hy >= GRID_HEIGHT:
                    self.game_over = True
                    return

            # obstacle collision
            if new_head in self.obstacles:
                self.game_over = True
                return

            # self collision
            if self.snake.collides_with_self():
                self.game_over = True
                return

            # apple collision
            if new_head == self.apple.pos:
                if self.apple.kind == "normal":
                    self.snake.grow()
                    self.score += 10
                    self.apples_eaten += 1
                else:  # golden
                    self.snake.grow(3)
                    self.score += 35
                    self.apples_eaten += 2
                self.spawn_apple()
                # level up for every 5 apples eaten (counts golden as 2)
                new_level = 1 + (self.apples_eaten // 5)
                if new_level > self.level:
                    self.level_up(new_level)

    def level_up(self, new_level):
        self.level = new_level
        self.move_interval = self.compute_move_interval()
        self.generate_obstacles()
        # small reward: spawn one extra growth
        self.snake.grow(1)

    def draw_grid(self, surface):
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if (x + y) % 2 == 0:
                    pygame.draw.rect(surface, (30, 30, 30), rect)
                else:
                    pygame.draw.rect(surface, (25, 25, 25), rect)

    def draw(self, surface):
        self.draw_grid(surface)
        # obstacles
        for o in self.obstacles:
            rect = pygame.Rect(o[0] * CELL_SIZE, o[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, (100, 50, 50), rect)
        # apple
        self.apple.draw(surface)
        # snake
        self.snake.draw(surface)
        # HUD
        hud_y = GRID_HEIGHT * CELL_SIZE
        pygame.draw.rect(surface, (10, 10, 10), (0, hud_y, WIDTH, 40))
        draw_text(surface, f"Score: {self.score}", 8, hud_y + 8)
        draw_text(surface, f"Level: {self.level}", 150, hud_y + 8)
        draw_text(surface, f"Snake: {self.snake.type_name}", 260, hud_y + 8)
        draw_text(surface, "P: Pause  R: Restart  Esc: Quit", 420, hud_y + 8)
        if self.paused:
            draw_text(surface, "PAUSED", WIDTH // 2 - 40, hud_y + 8, (200, 200, 0))
        if self.game_over:
            draw_text(surface, "GAME OVER - Press R to restart or Esc to quit", WIDTH // 2 - 220, hud_y + 8, (220, 20, 20))


def menu_select_snake():
    selected = 0
    types = list(SNAKE_TYPES.keys())
    while True:
        screen.fill((12, 12, 12))
        draw_text(screen, "Choose your snake type:", 20, 20)
        for i, name in enumerate(types):
            y = 60 + i * 30
            prefix = "-> " if i == selected else "   "
            draw_text(screen, f"{prefix}{name}", 40, y, (255, 255, 255) if i == selected else (150, 150, 150))
            # draw small preview
            color = SNAKE_TYPES[name]["color"]
            pygame.draw.rect(screen, color, (300, y, 24, 24))
        draw_text(screen, "Enter: Start   Up/Down: Select", 20, HEIGHT - 30)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(types)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(types)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return types[selected]
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        clock.tick(30)


def main():
    snake_type = menu_select_snake()
    game = Game(snake_type)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    game.snake.set_direction((-1, 0))
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.snake.set_direction((1, 0))
                elif event.key in (pygame.K_UP, pygame.K_w):
                    game.snake.set_direction((0, -1))
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.snake.set_direction((0, 1))
                elif event.key == pygame.K_p:
                    game.paused = not game.paused
                elif event.key == pygame.K_r:
                    # restart (keep same snake type and reset)
                    game = Game(game.snake.type_name)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        game.update()
        screen.fill((0, 0, 0))
        game.draw(screen)
        pygame.display.flip()
        # tick at a reasonable framerate
        clock.tick(60)


if __name__ == "__main__":
    main()