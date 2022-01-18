from random import uniform, gauss, choice
from functools import partial
from operator import attrgetter
from random import randint
import pygame
from constants import *


MULT = [
    [1, 0, 0, -1, -1, 0, 0, 1],
    [0, 1, -1, 0, 0, -1, 1, 0],
    [0, 1, 1, 0, 0, -1, -1, 0],
    [1, 0, 0, 1, -1, 0, 0, -1],
]


def get_visible_points(start_location, get_allows_light, max_distance=30):
    x, y = start_location
    line_of_sight = set()
    line_of_sight.add(start_location)
    blocked_set = set()
    distance = dict()
    distance[start_location] = 0
    for region in range(8):
        cast_light(line_of_sight, blocked_set, distance, get_allows_light, x, y, 1, 1, 0, max_distance,
                   MULT[0][region], MULT[1][region], MULT[2][region], MULT[3][region])
    return line_of_sight, blocked_set, distance


def cast_light(los_cache, blocked_set, distance, get_allows_light, cx, cy, row, start, end, radius, xx, xy, yx, yy):
    if start < end:
        return
    radius_squared = radius ** 2
    for j in range(row, radius + 1):
        dx, dy = -j - 1, -j
        blocked = False
        while dx <= 0:
            dx += 1
            point = cx + dx * xx + dy * xy, cy + dx * yx + dy * yy
            l_slope, r_slope = (dx - 0.5) / (dy + 0.5), (dx + 0.5) / (dy - 0.5)
            if start < r_slope:
                continue
            elif end > l_slope:
                break
            else:
                d = dx ** 2 + dy ** 2
                if d < radius_squared:
                    los_cache.add(point)
                    distance[point] = d
                if blocked:
                    if not get_allows_light(point):
                        new_start = r_slope
                        continue
                    else:
                        blocked = False
                        start = new_start
                else:
                    if not get_allows_light(point) and j < radius:
                        blocked = True
                        blocked_set.add(point)
                        distance[point] = d
                        cast_light(los_cache, blocked_set, distance, get_allows_light, cx, cy, j + 1, start, l_slope, radius,
                                   xx, xy, yx, yy)
                        new_start = r_slope
        if blocked:
            break


def draw_fog(fog_surface, light_surface, visible, distance, new_points, explored_value, light_radius2, cast_light_radius,light_mod_value):
    explored_color = explored_value, explored_value, explored_value
    white = 255, 255, 255
    circle = pygame.draw.circle
    fog_surface.lock()
    light_surface.lock()
    for point, size in new_points:
        circle(fog_surface, white, point, size)
    draw_list = list()
    for point in visible:
        draw_list.append((distance[point], point))
    draw_list.sort(reverse=True)
    cache = dict()
    light_surface.fill(explored_color)
    value_range = 255 - explored_value
    for d, point in draw_list:
        token = d // light_mod_value
        try:
            color = cache[token]
        except KeyError:
            value0 = 1 - (d / light_radius2)
            value = int(-1.0 * value0 * (value0 - 2.0) * value_range) + explored_value
            value = min(255, max(0, value))
            color = value, value, value
            cache[token] = color
        circle(light_surface, color, point, cast_light_radius)
    fog_surface.unlock()
    light_surface.unlock()
    light_surface.blit(fog_surface, (0, 0), special_flags=pygame.BLEND_MULT)


def light(fog_tiles, point):
    try:
        return fog_tiles[point[1]][point[0]]
    except IndexError:
        return False


def random_in_rect(rect):
    rect = pygame.Rect(rect)
    return pygame.Vector2(uniform(rect.left, rect.right), uniform(rect.top, rect.bottom))


def from_polar(rho, theta):
    v = pygame.Vector2()
    v.from_polar((rho, theta))
    return v


def clamp(value, min_value, max_value):
    if value < min_value:
        return min_value
    elif max_value < value:
        return max_value
    else:
        return value


def load_image(name: str, scale=1):
    image = pygame.image.load(f"{name}.png")
    if scale != 1:
        new_size = image.get_width() * scale, image.get_height() * scale
        image = pygame.transform.scale(image, new_size)
    return image.convert_alpha()


class GameObject:
    def __init__(self, pos, sprite: pygame.Surface):
        self.pos = pygame.Vector2(pos)
        self.size = pygame.Vector2(sprite.get_size())
        self.sprite = sprite
        self.mask = pygame.mask.from_surface(self.sprite)
        bounds = self.mask.get_bounding_rects()
        self.bbox = bounds[0].unionall(bounds[1:])
        self.hidden = False
        self.opacity = 255

    def __str__(self):
        return f"<{self.__class__.__name__}(pos={self.pos}, size={self.size})>"

    @property
    def rect(self):
        return pygame.Rect(self.pos, self.size)

    def render(self, screen):
        if not self.hidden:
            self.sprite.set_alpha(self.opacity)
            screen.blit(self.sprite, self.pos)

    def update(self):
        pass


class MoveableObject(GameObject):
    SCALE = 3
    SIZE = 16
    SHEET = "blue_ghost"

    ACCELERATION = 0.5
    DAMPING = 0.85

    def __init__(self, pos):
        self.velocity = pygame.Vector2()
        self.acceleration = pygame.Vector2()

        super().__init__(pos, self.get_image())

    def get_image(self):
        angle = self.velocity.as_polar()[1]
        idx = int((-angle + 90 + 45 / 2) % 360 / 360 * 8)
        sheet = load_image(self.SHEET, self.SCALE)
        unit = self.SIZE * self.SCALE
        image = sheet.subsurface(idx * unit, 0, unit, unit)
        self.mask = pygame.mask.from_surface(image)
        bounds = self.mask.get_bounding_rects()
        self.bbox = bounds[0].unionall(bounds[1:])
        return image


class Player(MoveableObject):
    def update(self):
        pressed = pygame.key.get_pressed()
        direction_x = pressed[pygame.K_RIGHT] - pressed[pygame.K_LEFT]
        direction_y = pressed[pygame.K_DOWN] - pressed[pygame.K_UP]

        self.acceleration = pygame.Vector2(direction_x, direction_y) * self.ACCELERATION
        self.velocity *= self.DAMPING
        self.velocity += self.acceleration
        new_pos = self.pos + self.velocity
        self.sprite = self.get_image()
        new_pos = pygame.Vector2(clamp(new_pos.x, 0, SIZE[0] - self.rect.width),
                                 clamp(new_pos.y, 0, SIZE[1] - self.rect.height))
        self.pos = new_pos


class Ghost(MoveableObject):
    SHEET = "pink_ghost"
    ACCELERATION = 0.2
    DAMPING = 0.9

    def __init__(self, pos=None):
        if pos is None:
            pos = random_in_rect(pygame.Rect(0, 0, *SIZE))
        super().__init__(pos)
        self.goal = self.new_goal()

    def new_goal(self):
        direction = from_polar(60, gauss(self.velocity.as_polar()[1], 30))
        return self.rect.center + direction

    def update(self):
        middle_area = pygame.Rect(0, 0, *SIZE).inflate(-30, -30)
        while self.rect.collidepoint(self.goal) or not middle_area.collidepoint(self.goal):
            self.goal = self.new_goal()

        self.acceleration = (self.goal - self.rect.center).normalize() * self.ACCELERATION
        self.velocity *= self.DAMPING
        self.velocity += self.acceleration
        new_pos = self.pos + self.velocity
        self.sprite = self.get_image()
        new_pos = pygame.Vector2(clamp(new_pos.x, 0, SIZE[0] - self.rect.width),
                                 clamp(new_pos.y, 0, SIZE[1] - self.rect.height))
        self.pos = new_pos


class SolidObject(GameObject):
    SHEET_RECT = [
        (0, 0, 24, 31),
        (24, 0, 24, 24),
        (48, 0, 24, 24),
        (72, 0, 16, 24),
        (88, 0, 48, 43),
        (136, 0, 16, 16),
    ]
    SCALE = 3

    def __init__(self, pos, collision_rect=None):
        sheet = load_image("tileset", self.SCALE)
        sheet.set_colorkey(0xFFFFFF)
        rect = choice(self.SHEET_RECT)
        rect = [x * self.SCALE for x in rect]
        self.collision_rect = collision_rect
        super().__init__(pos, sheet.subsurface(rect))

    @classmethod
    def generate_many(cls, nb=16, max_tries=1000):
        objects = []
        tries = 0
        while len(objects) < nb and tries < max_tries:
            pos = random_in_rect(pygame.Rect(120, 120, *SIZE))
            obj = cls(pos)
            if not any(obj.rect.colliderect(other.rect) for other in objects):
                objects.append(obj)
        return objects


class GameObjects:
    def __init__(self):
        self.objects = []

    def add_object(self, obj):
        self.objects.append(obj)

    def update(self):
        for obj in self.objects:
            obj.update()

    def render(self, screen):
        for obj in self.objects:
            obj.render(screen)


class Program:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SIZE)
        self.running = True
        self.clock = pygame.time.Clock()
        self.objects = GameObjects()
        self.player = Player((100, 100))
        self.ghosts = [Ghost() for _ in range(16)]
        self.objects.add_object(self.player)
        self.obstacles = SolidObject.generate_many(36)
        for ghost in self.ghosts:
            self.objects.add_object(ghost)
        for obstacle in self.obstacles:
            self.objects.add_object(obstacle)

    def update(self):
        self.objects.update()

    def render(self):
        self.screen.fill((102, 183, 108))
        for obj in sorted(self.objects.objects, key=attrgetter("rect.bottom")):
            obj.render(self.screen)

    def mainloop(self):
        new_points = set()
        cast_light = None
        blocked_light_min = None
        blocked_light_max = None
        unblocked_light_min = None
        unblocked_light_max = None
        old_screen = None
        work_surface = None
        fog_tiles = None
        fog_table = None
        fog_surface = None
        light_surface = None

        while self.running:
            if pygame.event.get(pygame.QUIT):
                self.running = False

            sw, sh = self.screen.get_size()
            stw = sw // cell_size_px
            sth = sh // cell_size_px

            if old_screen is not self.screen:
                old_screen = self.screen
                fog_size = sw // cell_size_px, sh // cell_size_px
                work_surface = pygame.surface.Surface((sw, sh))
                fog_surface = pygame.surface.Surface(fog_size)
                light_surface = pygame.surface.Surface(fog_size)
                blocked_light_min = max(1, blocked_expose_min_px // cell_size_px)
                blocked_light_max = max(1, blocked_expose_max_px // cell_size_px)
                unblocked_light_min = max(1, unblocked_expose_min_px // cell_size_px)
                unblocked_light_max = max(1, unblocked_expose_max_px // cell_size_px)
                cast_light = max(1, cast_light_px // cell_size_px)
                fog_table = dict()
                fog_tiles = list()
                for y in range(0, sth * cell_size_px, cell_size_px):
                    row = list()
                    fog_tiles.append(row)
                    for x in range(0, stw * cell_size_px, cell_size_px):
                        row.append(False)

            self.update()

            for row in fog_tiles:
                for x in range(len(row)):
                    row[x] = True
            for obj in self.objects.objects:
                if obj is self.player or obj in self.ghosts:
                    continue
                rect = obj.bbox.move(obj.rect.topleft)
                left = rect.left // cell_size_px
                top = rect.top // cell_size_px
                right = rect.right // cell_size_px
                bottom = rect.bottom // cell_size_px
                for y in range(top, bottom + 1):
                    for x in range(left, right + 1):
                        try:
                            fog_tiles[y][x] = False
                        except IndexError:
                            pass

            x1, y1 = self.player.rect.center
            for ghost in self.ghosts:
                x2, y2 = ghost.rect.center
                d2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
                if d2 < light_radius_px2:
                    opacity = 1 - (d2 / light_radius_px2)
                    opacity = int(-1.0 * opacity * (opacity - 2.0) * 255)
                    opacity = min(255, max(0, opacity))
                    ghost.hidden = False
                    ghost.opacity = opacity
                else:
                    ghost.hidden = True

            px = self.player.rect.centerx // cell_size_px
            py = self.player.rect.centery // cell_size_px
            visible, blocked, distance = get_visible_points((px, py), partial(light, fog_tiles), light_radius)

            new_points.clear()
            for point in blocked:
                if point not in fog_table:
                    size = randint(blocked_light_min, blocked_light_max)
                    fog_table[point] = size
                    new_points.add((point, size))
            for point in visible:
                if point not in fog_table:
                    size = randint(unblocked_light_min, unblocked_light_max)
                    fog_table[point] = size
                    new_points.add((point, size))

            draw_fog(fog_surface, light_surface, visible, distance, new_points, explored_value, light_radius2, cast_light, light_mod_value)

            self.render()
            pygame.transform.scale(light_surface, work_surface.get_size(), work_surface)
            self.screen.blit(work_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            pygame.display.flip()
            pygame.display.set_caption(f"{self.clock.get_fps():.2f}")
            self.clock.tick(60)


if __name__ == '__main__':
    p = Program()
    p.mainloop()
