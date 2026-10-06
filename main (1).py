import math
import random
import pygame
import asyncio

pygame.init()

# Use the full desktop resolution so the HUD and play area are always visible.
WIDTH, HEIGHT = pygame.display.get_desktop_sizes()[0]

# A fixed seed makes the initial scene reproducible while keeping each vector unique.
random.seed(17)
FPS = 60
ASTEROID_COUNT = 8


BACKGROUND = (9, 13, 24)
MISSILE_SPEED = 360
MISSILE_RADIUS = 5
SHIP_POSITION = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
SHIP_ANGLE = 90
ROTATION_SPEED = 3
THRUST = 0.15
DRAG = 0.99
MAX_SPEED = 7
MISSILE_COOLDOWN = 0.2
DETECTION_RANGE = 300
FOV_THRESHOLD = 0.7
FOV_PRESETS = (0.0, 0.5, 0.7, 0.9)
ENEMY_SCAN_SPEED = 30  # degrees per second (0.5 degrees per frame at 60 FPS)
ENEMY_FIRE_COOLDOWN = 1.2
WHITE = (255, 255, 255)
RED = (255, 80, 80)
YELLOW = (255, 225, 120)
GRAY = (105, 115, 135)
ENEMY_MISSILE_COLOR = (255, 100, 170)


async def main():

class Asteroid:
    def __init__(self, position, radius, velocity, color, shape_points):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.radius = radius
        # For a uniform circular body, mass is proportional to area.
        self.mass = radius * radius
        self.inverse_mass = 1.0 / self.mass
        self.color = color
        self.shape_points = shape_points
        self.angle = random.uniform(0, math.tau)
        self.spin = random.uniform(-0.7, 0.7)


    def update(self, dt):
        self.position += self.velocity * dt
        self.angle += self.spin * dt


        # Screen-edge wrapping keeps all asteroids in motion indefinitely.
        if self.position.x < -self.radius:
            self.position.x = WIDTH + self.radius
        elif self.position.x > WIDTH + self.radius:
            self.position.x = -self.radius
        if self.position.y < -self.radius:
            self.position.y = HEIGHT + self.radius
        elif self.position.y > HEIGHT + self.radius:
            self.position.y = -self.radius


    def draw(self, surface):
        points = []
        cosine = math.cos(self.angle)
        sine = math.sin(self.angle)
        for x, y in self.shape_points:
            rotated_x = x * cosine - y * sine
            rotated_y = x * sine + y * cosine
            points.append((self.position.x + rotated_x, self.position.y + rotated_y))
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (185, 195, 215), points, 2)




class Rocket:
    def __init__(self, position, angle):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        self.angle = angle
        self.is_thrusting = False

    def forward(self):
        radians = math.radians(self.angle)
        return pygame.Vector2(math.cos(radians), -math.sin(radians))

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += ROTATION_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= ROTATION_SPEED

        self.acceleration = pygame.Vector2(0, 0)
        self.is_thrusting = False
        direction = self.forward()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.acceleration = direction * THRUST
            self.is_thrusting = True
        if keys[pygame.K_DOWN]:
            self.acceleration = -direction * THRUST
            self.is_thrusting = True

        self.velocity += self.acceleration
        self.velocity *= DRAG
        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)
        self.position += self.velocity

        self.position.x %= WIDTH
        self.position.y %= HEIGHT

    def draw(self, surface):
        direction = self.forward()
        left = direction.rotate(140)
        right = direction.rotate(-140)
        p1 = self.position + direction * 22
        p2 = self.position + left * 16
        p3 = self.position + right * 16
        if self.is_thrusting:
            back = self.position - direction * 18
            pygame.draw.circle(surface, YELLOW, back, 5)
        pygame.draw.polygon(surface, (80, 170, 235), [p1, p2, p3])
        pygame.draw.polygon(surface, WHITE, [p1, p2, p3], 2)


class Enemy:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.angle = 0

    def forward(self):
        radians = math.radians(self.angle)
        return pygame.Vector2(math.cos(radians), -math.sin(radians))

    def draw(self, surface, detected):
        color = RED if detected else WHITE
        direction = self.forward()
        left = direction.rotate(140)
        right = direction.rotate(-140)
        points = [
            self.position + direction * 24,
            self.position + left * 17,
            self.position + right * 17,
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (185, 195, 215), points, 2)


class Missile:
    def __init__(self, start, direction, color=YELLOW):
        self.position = pygame.Vector2(start)
        self.radius = MISSILE_RADIUS
        self.velocity = pygame.Vector2(direction).normalize() * MISSILE_SPEED
        self.color = color

    def update(self, dt):
        self.position += self.velocity * dt

    def is_off_screen(self):
        return (
            self.position.x < -MISSILE_RADIUS
            or self.position.x > WIDTH + MISSILE_RADIUS
            or self.position.y < -MISSILE_RADIUS
            or self.position.y > HEIGHT + MISSILE_RADIUS
        )

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.position, MISSILE_RADIUS)
        pygame.draw.circle(surface, (255, 245, 190), self.position, 2)



def make_asteroid(index):
    radius = random.randint(25, 48)
    # Ensure starting positions do not overlap.
    while True:
        position = pygame.Vector2(
            random.uniform(radius, WIDTH - radius),
            random.uniform(radius, HEIGHT - radius),
        )
        if all(position.distance_to(other.position) > radius + other.radius + 12
               for other in asteroids):
            break


    # Distinct direction and speed for every asteroid.
    speed = 55 + index * 24 + random.uniform(-5, 5)
    direction = random.uniform(0, math.tau)
    velocity = pygame.Vector2(math.cos(direction), math.sin(direction)) * speed
    color = random.choice([(116, 132, 156), (133, 126, 105), (105, 145, 137), (145, 116, 130)])


    vertices = random.randint(8, 11)
    shape = []
    for vertex in range(vertices):
        angle = math.tau * vertex / vertices
        uneven_radius = radius * random.uniform(0.78, 1.16)
        shape.append((math.cos(angle) * uneven_radius, math.sin(angle) * uneven_radius))
    return Asteroid(position, radius, velocity, color, shape)




def resolve_collision(first, second):
    offset = second.position - first.position
    distance_squared = offset.length_squared()
    minimum_distance = first.radius + second.radius


    if distance_squared >= minimum_distance * minimum_distance:
        return


    if distance_squared < 0.000001:
        # A deterministic fallback for the extremely unlikely exact-center case.
        normal = pygame.Vector2(1, 0)
        distance = 0.0
    else:
        distance = math.sqrt(distance_squared)
        normal = offset / distance


    # Separate overlapping bodies first, weighted by inverse mass.
    overlap = minimum_distance - distance
    inverse_mass_total = first.inverse_mass + second.inverse_mass
    first.position -= normal * overlap * (first.inverse_mass / inverse_mass_total)
    second.position += normal * overlap * (second.inverse_mass / inverse_mass_total)


    # Relative velocity along the collision normal tells whether bodies approach.
    relative_velocity = second.velocity - first.velocity
    velocity_along_normal = relative_velocity.dot(normal)
    if velocity_along_normal >= 0:
        return


    # Perfectly elastic impulse: momentum and kinetic energy are conserved.
    restitution = 1.0
    impulse_size = -(1 + restitution) * velocity_along_normal / inverse_mass_total
    impulse = normal * impulse_size
    first.velocity -= impulse * first.inverse_mass
    second.velocity += impulse * second.inverse_mass




pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Rotating Spaceship Controller")
clock = pygame.time.Clock()
asteroids = []
for asteroid_index in range(ASTEROID_COUNT):
    asteroids.append(make_asteroid(asteroid_index))
missiles = []
enemy_missiles = []
rocket = Rocket(SHIP_POSITION, SHIP_ANGLE)
enemy = Enemy((WIDTH / 4, HEIGHT / 2))
score = 0
player_hp = 10
player_damage = 0
fire_timer = 0.0
enemy_fire_timer = 0.0
font = pygame.font.Font(None, 30)
score_font = pygame.font.Font(None, 48)


running = True
while running:
    dt = min(clock.tick(FPS) / 1000.0, 0.035)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                FOV_THRESHOLD = FOV_PRESETS[event.key - pygame.K_1]


    rocket.update()
    enemy.angle = (enemy.angle + ENEMY_SCAN_SPEED * dt) % 360

    # Compare the enemy's facing direction with the normalized direction to the player.
    enemy_forward = enemy.forward()
    to_player = rocket.position - enemy.position
    distance = to_player.length()
    dot = 0.0
    if distance > 0:
        dot = enemy_forward.dot(to_player.normalize())
    detected = distance < DETECTION_RANGE and dot > FOV_THRESHOLD
    enemy_state = "ATTACK" if detected else "PATROL"

    fire_timer -= dt
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE] and fire_timer <= 0:
        direction = rocket.forward()
        missile_start = rocket.position + direction * 25
        missiles.append(Missile(missile_start, direction))
        fire_timer = MISSILE_COOLDOWN

    enemy_fire_timer -= dt
    if detected and distance > 0 and enemy_fire_timer <= 0:
        direction = to_player.normalize()
        missile_start = enemy.position + direction * 25
        enemy_missiles.append(Missile(missile_start, direction, ENEMY_MISSILE_COLOR))
        enemy_fire_timer = ENEMY_FIRE_COOLDOWN

    for asteroid in asteroids:
        asteroid.update(dt)
    for missile in missiles:
        missile.update(dt)
    for missile in enemy_missiles:
        missile.update(dt)

    # Enemy missile hits remove one HP and increment the player's damage counter.
    remaining_enemy_missiles = []
    for missile in enemy_missiles:
        if missile.position.distance_to(rocket.position) <= missile.radius + 20:
            player_hp = max(0, player_hp - 1)
            player_damage += 1
        elif not missile.is_off_screen():
            remaining_enemy_missiles.append(missile)
    enemy_missiles = remaining_enemy_missiles

    # Check each missile against every asteroid and remove both on impact.
    remaining_missiles = []
    for missile in missiles:
        if missile.is_off_screen():
            continue

        hit_asteroid = None
        for asteroid in asteroids:
            distance = missile.position.distance_to(asteroid.position)
            if distance < missile.radius + asteroid.radius:
                hit_asteroid = asteroid
                break

        if hit_asteroid is None:
            remaining_missiles.append(missile)
        else:
            # Replace the hit asteroid immediately so the asteroid count stays constant.
            asteroids.remove(hit_asteroid)
            asteroids.append(make_asteroid(len(asteroids)))
            score += 1

    missiles = remaining_missiles


    # Multiple passes help resolve clusters of simultaneous contacts.
    for _ in range(3):
        for first_index in range(len(asteroids)):
            for second_index in range(first_index + 1, len(asteroids)):
                resolve_collision(asteroids[first_index], asteroids[second_index])


    screen.fill(BACKGROUND)
    pygame.draw.circle(
        screen, GRAY, (round(enemy.position.x), round(enemy.position.y)),
        DETECTION_RANGE, 1
    )
    for asteroid in asteroids:
        asteroid.draw(screen)
    for missile in missiles:
        missile.draw(screen)
    for missile in enemy_missiles:
        missile.draw(screen)
    rocket.draw(screen)
    enemy.draw(screen, detected)
    pygame.draw.line(
        screen, RED, enemy.position, enemy.position + enemy_forward * 100, 3
    )
    forward = rocket.forward()
    pygame.draw.line(screen, RED, rocket.position, rocket.position + forward * 70, 3)
    pygame.draw.line(
        screen, YELLOW, rocket.position, rocket.position + rocket.velocity * 10, 3
    )

    angle_text = font.render(f"Angle: {rocket.angle:.0f}°", True, WHITE)
    vector_text = font.render(
        f"Forward: ({forward.x:.2f}, {forward.y:.2f})", True, WHITE
    )
    speed_text = font.render(f"Speed: {rocket.velocity.length():.2f}", True, WHITE)
    velocity_text = font.render(
        f"Velocity: ({rocket.velocity.x:.2f}, {rocket.velocity.y:.2f})",
        True,
        WHITE,
    )
    distance_text = font.render(f"Distance: {distance:.1f}", True, WHITE)
    dot_text = font.render(f"Dot Product: {dot:.2f}", True, WHITE)
    state_color = RED if detected else WHITE
    state_text = font.render(f"Enemy State: {enemy_state}", True, state_color)
    threshold_text = font.render(f"FOV Threshold: {FOV_THRESHOLD:.1f} (press 1-4)", True, WHITE)
    health_color = RED if player_hp <= 3 else WHITE
    health_text = font.render(f"HP: {player_hp}/10   Damage Taken: {player_damage}", True, health_color)
    controls_text = font.render(
        "LEFT/A RIGHT/D: turn   UP/W: thrust   DOWN: reverse   SPACE: fire   1-4: FOV",
        True,
        (180, 190, 210),
    )
    screen.blit(angle_text, (15, 15))
    screen.blit(vector_text, (15, 43))
    screen.blit(speed_text, (15, 71))
    screen.blit(velocity_text, (15, 99))
    screen.blit(distance_text, (15, 127))
    screen.blit(dot_text, (15, 155))
    screen.blit(state_text, (15, 183))
    screen.blit(threshold_text, (15, 211))
    screen.blit(health_text, (15, 239))
    screen.blit(controls_text, (15, HEIGHT - 35))

    score_text = score_font.render(f"ASTEROIDS HIT: {score:03d}", True, (255, 225, 120))
    score_shadow = score_font.render(f"ASTEROIDS HIT: {score:03d}", True, (35, 40, 60))
    screen.blit(score_shadow, (WIDTH - score_text.get_width() - 13, 17))
    screen.blit(score_text, (WIDTH - score_text.get_width() - 15, 15))
    pygame.display.flip()
    clock.tick(60)
    await asyncio.sleep(0)

pygame.quit()
asyncio.run(main())


