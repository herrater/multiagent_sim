import pygame
import random
import sys

# Inicjalizacja Pygame
pygame.init()

# Ustawienia okna
WIDTH, HEIGHT = 800, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Symulacja ruchu drogowego")

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)
YELLOW = (255, 255, 0)

# Parametry
FPS = 60
LIGHT_CYCLE = 300
CAR_SIZE = 20
PEDESTRIAN_SIZE = 10

# Strefa bezpieczeństwa między pieszym a samochodem
SAFETY_BUFFER = 10


# Klasy pomocnicze
class TrafficLight:
    def __init__(self):
        self.timer = 0
        self.state = 'NS'  # NS zielone dla pojazdów jadących z północy i południa
        self.pedestrian_state = 'NS'  # synchronizacja pieszych z pojazdami

    def update(self):
        self.timer += 1
        if self.timer >= LIGHT_CYCLE:
            self.timer = 0
            if self.state == 'NS':
                self.state = 'EW'
                self.pedestrian_state = 'EW'
            else:
                self.state = 'NS'
                self.pedestrian_state = 'NS'

    def vehicle_green(self, direction):
        if direction in ['N', 'S']:
            return self.state == 'NS'
        else:
            return self.state == 'EW'

    def pedestrian_green(self, crossing):
        # crossing: 'NS', 'SN', 'EW', 'WE'
        if crossing in ['NS', 'SN']:
            return self.pedestrian_state == 'NS'
        else:
            return self.pedestrian_state == 'EW'


class Car:
    car_id_counter = 0

    def __init__(self, direction):
        self.direction = direction
        self.speed = 2
        self.passed_light = False
        self.id = Car.car_id_counter
        Car.car_id_counter += 1

        # Decyzja o prawoskręcie (30% szans) i flaga zakończenia skrętu
        self.turn_right_decided = False
        self.turn_right = False
        self.has_turned = False

        # Współrzędne początkowe zgodnie z ruchem prawostronnym:
        if direction == 'N':
            self.x = WIDTH // 2 + 10
            self.y = HEIGHT
        elif direction == 'S':
            self.x = WIDTH // 2 - 30
            self.y = -CAR_SIZE
        elif direction == 'E':
            self.x = -CAR_SIZE
            self.y = HEIGHT // 2 + 10
        elif direction == 'W':
            self.x = WIDTH
            self.y = HEIGHT // 2 - 30

    def move(self, light, others, pedestrians):
        # Decyzja o skręcie w prawo, jeśli jeszcze nie podjęta
        if not self.turn_right_decided:
            self.turn_right_decided = True
            self.turn_right = random.random() < 0.3  # 30% szans na skręt

        stop = False
        OFFSET = 100

        # --- SPRAWDZENIE ŚWIATEŁ (tylko jeśli jeszcze nie minął punktu krytycznego) ---
        if not self.has_turned:
            if self.direction == 'N':
                light_pos = HEIGHT // 2 + 10 + OFFSET
                if (not self.passed_light) and (self.y <= light_pos) and (not light.vehicle_green('N')):
                    stop = True
                elif (not self.passed_light) and (self.y < HEIGHT // 2 + 10):
                    self.passed_light = True
            elif self.direction == 'S':
                light_pos = HEIGHT // 2 - 10 - OFFSET
                if (not self.passed_light) and (self.y + CAR_SIZE >= light_pos) and (not light.vehicle_green('S')):
                    stop = True
                elif (not self.passed_light) and (self.y + CAR_SIZE > HEIGHT // 2 - 10):
                    self.passed_light = True
            elif self.direction == 'E':
                light_pos = WIDTH // 2 - 10 - OFFSET
                if (not self.passed_light) and (self.x + CAR_SIZE >= light_pos) and (not light.vehicle_green('E')):
                    stop = True
                elif (not self.passed_light) and (self.x + CAR_SIZE > WIDTH // 2 - 10):
                    self.passed_light = True
            elif self.direction == 'W':
                light_pos = WIDTH // 2 + 10 + OFFSET
                if (not self.passed_light) and (self.x <= light_pos) and (not light.vehicle_green('W')):
                    stop = True
                elif (not self.passed_light) and (self.x < WIDTH // 2 + 10):
                    self.passed_light = True

        # --- UNIKANIE KOLIZJI Z INNYMI POJAZDAMI jadącymi w tym samym kierunku ---
        for other in others:
            if other == self or other.direction != self.direction:
                continue
            if self.direction == 'N' and 0 < self.y - other.y < CAR_SIZE + 5 and abs(self.x - other.x) < 5:
                stop = True
            elif self.direction == 'S' and 0 < other.y - self.y < CAR_SIZE + 5 and abs(self.x - other.x) < 5:
                stop = True
            elif self.direction == 'E' and 0 < other.x - self.x < CAR_SIZE + 5 and abs(self.y - other.y) < 5:
                stop = True
            elif self.direction == 'W' and 0 < self.x - other.x < CAR_SIZE + 5 and abs(self.y - other.y) < 5:
                stop = True

        # --- UNIKANIE ZBYT BLISKIEGO KONTAKTU Z PIESZYMI ---
        for ped in pedestrians:
            dx = ped.x - (self.x + CAR_SIZE / 2)
            dy = ped.y - (self.y + CAR_SIZE / 2)
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance < CAR_SIZE / 2 + PEDESTRIAN_SIZE:
                stop = True

        if stop:
            return
        

        # --- LOGIKA SKRĘTU W PRAWO (dopasowana, by jechać po ćwiartce skrzyżowania, nie środku) ---
        if self.turn_right and not self.has_turned:
            # Faza dojazdu do sygnalizatora
            if self.direction == 'N':
                if not self.passed_light:
                    self.y -= self.speed
                else:
                    # Po minięciu sygnalizatora skręcamy w prawo: jedziemy na wschód
                    if self.x < WIDTH // 2 + 60:
                        self.x += self.speed
                    else:
                        self.has_turned = True
                        self.direction = 'E'
            elif self.direction == 'E':
                if not self.passed_light:
                    self.x += self.speed
                else:
                    # Po minięciu sygnalizatora skręcamy w prawo: jedziemy na południe
                    if self.y < HEIGHT // 2 + 60:
                        self.y += self.speed
                    else:
                        self.has_turned = True
                        self.direction = 'S'
            elif self.direction == 'S':
                if not self.passed_light:
                    self.y += self.speed
                else:
                    # Skręt w prawo: jedziemy na zachód
                    if self.x > WIDTH // 2 - 60:
                        self.x -= self.speed
                    else:
                        self.has_turned = True
                        self.direction = 'W'
            elif self.direction == 'W':
                if not self.passed_light:
                    self.x -= self.speed
                else:
                    # Skręt w prawo: jedziemy na północ
                    if self.y > HEIGHT // 2 - 60:
                        self.y -= self.speed
                    else:
                        self.has_turned = True
                        self.direction = 'N'
        else:
            # --- JAZDA PROSTO (lub po ukończeniu skrętu) ---
            if self.direction == 'N':
                self.y -= self.speed
            elif self.direction == 'S':
                self.y += self.speed
            elif self.direction == 'E':
                self.x += self.speed
            elif self.direction == 'W':
                self.x -= self.speed

    def draw(self, win):
        pygame.draw.rect(win, BLUE, (self.x, self.y, CAR_SIZE, CAR_SIZE))
        font = pygame.font.SysFont(None, 14)
        text = font.render(str(self.id), True, WHITE)
        win.blit(text, (self.x, self.y))


class Pedestrian:
    pedestrian_id_counter = 0

    def __init__(self, crossing):
        self.crossing = crossing
        self.speed = 1
        self.passed_light = False
        self.id = Pedestrian.pedestrian_id_counter
        Pedestrian.pedestrian_id_counter += 1

        if crossing == 'NS':
            self.x = WIDTH // 2 - 70
            self.y = HEIGHT // 2 + 80
        elif crossing == 'SN':
            self.x = WIDTH // 2 + 70
            self.y = HEIGHT // 2 - 80
        elif crossing == 'EW':
            self.x = WIDTH // 2 - 80
            self.y = HEIGHT // 2 - 70
        elif crossing == 'WE':
            self.x = WIDTH // 2 + 80
            self.y = HEIGHT // 2 + 70

    def move(self, light):
        if self.passed_light:
            dx, dy = 0, 0
            if self.crossing == 'NS':
                dy = -self.speed
            elif self.crossing == 'SN':
                dy = self.speed
            elif self.crossing == 'EW':
                dx = self.speed
            elif self.crossing == 'WE':
                dx = -self.speed
            self.x += dx
            self.y += dy
        else:
            if light.pedestrian_green(self.crossing):
                dx, dy = 0, 0
                if self.crossing == 'NS':
                    dy = -self.speed
                elif self.crossing == 'SN':
                    dy = self.speed
                elif self.crossing == 'EW':
                    dx = self.speed
                elif self.crossing == 'WE':
                    dx = -self.speed
                self.x += dx
                self.y += dy

                if (
                    (self.crossing == 'NS' and self.y <= HEIGHT // 2 + 40) or
                    (self.crossing == 'SN' and self.y >= HEIGHT // 2 - 40) or
                    (self.crossing == 'EW' and self.x >= WIDTH // 2 - 40) or
                    (self.crossing == 'WE' and self.x <= WIDTH // 2 + 40)
                ):
                    self.passed_light = True

    def draw(self, win):
        pygame.draw.circle(win, YELLOW, (int(self.x), int(self.y)), PEDESTRIAN_SIZE)
        font = pygame.font.SysFont(None, 14)
        text = font.render(str(self.id), True, BLACK)
        win.blit(text, (self.x - 5, self.y - 5))


def detect_pedestrian_collisions(pedestrians, cars):
    collisions = []
    remaining_pedestrians = []
    for ped in pedestrians:
        collision_occurred = False
        for car in cars:
            dx = ped.x - (car.x + CAR_SIZE / 2)
            dy = ped.y - (car.y + CAR_SIZE / 2)
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance < CAR_SIZE / 2 + PEDESTRIAN_SIZE:
                collisions.append((ped.x, ped.y))
                collision_occurred = True
                break
        if not collision_occurred:
            remaining_pedestrians.append(ped)
    return collisions, remaining_pedestrians


def detect_car_collisions(cars, active_pairs):
    """
    Zwraca (nowe_kolizje, aktualne_pary) gdzie:
    - nowe_kolizje: liczba par, które właśnie zaczęły się zderzać (wcześniej nie były w active_pairs)
    - aktualne_pary: zbiór frozenset({id1, id2}) dla wszystkich par kolidujących w tej klatce
    """
    new_collisions = 0
    current_pairs = set()

    n = len(cars)
    for i in range(n):
        for j in range(i + 1, n):
            car1 = cars[i]
            car2 = cars[j]
            dx = (car1.x + CAR_SIZE / 2) - (car2.x + CAR_SIZE / 2)
            dy = (car1.y + CAR_SIZE / 2) - (car2.y + CAR_SIZE / 2)
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance < CAR_SIZE:  # kolizja, gdy prostokąty zachodzą na siebie
                pair = frozenset({car1.id, car2.id})
                current_pairs.add(pair)
                if pair not in active_pairs:
                    new_collisions += 1

    return new_collisions, current_pairs


def draw_intersection(win, light, cars, pedestrians, ped_collisions, car_collisions, elapsed_seconds):
    win.fill(GRAY)
    pygame.draw.rect(win, BLACK, (WIDTH // 2 - 40, 0, 80, HEIGHT))
    pygame.draw.rect(win, BLACK, (0, HEIGHT // 2 - 40, WIDTH, 80))

    pygame.draw.rect(win, WHITE, (WIDTH // 2 - 90, HEIGHT // 2 - 45, 20, 90))
    pygame.draw.rect(win, WHITE, (WIDTH // 2 + 70, HEIGHT // 2 - 45, 20, 90))
    pygame.draw.rect(win, WHITE, (WIDTH // 2 - 45, HEIGHT // 2 - 90, 90, 20))
    pygame.draw.rect(win, WHITE, (WIDTH // 2 - 45, HEIGHT // 2 + 70, 90, 20))

    font = pygame.font.SysFont(None, 36)

    # Światła dla pojazdów
    if light.state == 'NS':
        pygame.draw.circle(win, GREEN, (WIDTH // 2 - 15, HEIGHT // 2 + 30), 10)
        pygame.draw.circle(win, GREEN, (WIDTH // 2 + 15, HEIGHT // 2 - 30), 10)
        pygame.draw.circle(win, RED, (WIDTH // 2 + 30, HEIGHT // 2 + 15), 10)
        pygame.draw.circle(win, RED, (WIDTH // 2 - 30, HEIGHT // 2 - 15), 10)
    else:
        pygame.draw.circle(win, RED, (WIDTH // 2 - 15, HEIGHT // 2 + 30), 10)
        pygame.draw.circle(win, RED, (WIDTH // 2 + 15, HEIGHT // 2 - 30), 10)
        pygame.draw.circle(win, GREEN, (WIDTH // 2 + 30, HEIGHT // 2 + 15), 10)
        pygame.draw.circle(win, GREEN, (WIDTH // 2 - 30, HEIGHT // 2 - 15), 10)

    # Światła dla pieszych
    if light.pedestrian_state == 'NS':
        pygame.draw.rect(win, GREEN, (WIDTH // 2 - 60, HEIGHT // 2 + 50, 20, 20))
        pygame.draw.rect(win, GREEN, (WIDTH // 2 + 50, HEIGHT // 2 - 60, 20, 20))
        pygame.draw.rect(win, RED, (WIDTH // 2 - 60, HEIGHT // 2 - 60, 20, 20))
        pygame.draw.rect(win, RED, (WIDTH // 2 + 50, HEIGHT // 2 + 50, 20, 20))
    else:
        pygame.draw.rect(win, RED, (WIDTH // 2 - 60, HEIGHT // 2 + 50, 20, 20))
        pygame.draw.rect(win, RED, (WIDTH // 2 + 50, HEIGHT // 2 - 60, 20, 20))
        pygame.draw.rect(win, GREEN, (WIDTH // 2 - 60, HEIGHT // 2 - 60, 20, 20))
        pygame.draw.rect(win, GREEN, (WIDTH // 2 + 50, HEIGHT // 2 + 50, 20, 20))

    # Rysowanie pojazdów i pieszych
    for car in cars:
        car.draw(win)
    for ped in pedestrians:
        ped.draw(win)

    # Wyświetlanie liczników kolizji i czasu
    text_ped = font.render(f"Kolizje pieszych: {ped_collisions}", True, BLACK)
    text_car = font.render(f"Kolizje pojazdów: {car_collisions}", True, BLACK)
    text_time = font.render(f"Czas: {elapsed_seconds} s", True, BLACK)
    win.blit(text_ped, (10, 10))
    win.blit(text_car, (10, 50))
    win.blit(text_time, (10, 90))

    pygame.display.update()


def main():
    clock = pygame.time.Clock()
    light = TrafficLight()
    cars = []
    pedestrians = []
    ped_collision_count = 0
    car_collision_count = 0
    active_car_pairs = set()  # zestaw aktualnie kolidujących par (frozenset z dwóch IDs)

    SPAWN_CAR_EVENT = pygame.USEREVENT + 1
    SPAWN_PED_EVENT = pygame.USEREVENT + 2
    pygame.time.set_timer(SPAWN_CAR_EVENT, 1500)
    pygame.time.set_timer(SPAWN_PED_EVENT, 3000)

    start_ticks = pygame.time.get_ticks()  # czas startu w ms

    running = True
    while running:
        clock.tick(FPS)
        light.update()

        # Oblicz czas upłynięty w sekundach
        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        # Jeśli minęły 2 minuty (120 s), zakończ symulację i wypisz wyniki
        if elapsed_seconds >= 60:
            print("Symulacja zakończona po 120 s.")
            print(f"Liczba kolizji pieszych: {ped_collision_count}")
            print(f"Liczba kolizji pojazdów: {car_collision_count}")
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == SPAWN_CAR_EVENT:
                direction = random.choice(['N', 'S', 'E', 'W'])
                cars.append(Car(direction))
            elif event.type == SPAWN_PED_EVENT:
                crossing = random.choice(['NS', 'SN', 'EW', 'WE'])
                pedestrians.append(Pedestrian(crossing))

        # Ruch pojazdów
        for car in cars:
            car.move(light, cars, pedestrians)

        # Ruch pieszych
        for ped in pedestrians:
            ped.move(light)

        # Detekcja kolizji pieszych
        ped_collisions, pedestrians = detect_pedestrian_collisions(pedestrians, cars)
        ped_collision_count += len(ped_collisions)

        # Detekcja kolizji pojazdów
        new_car_hits, current_pairs = detect_car_collisions(cars, active_car_pairs)
        car_collision_count += new_car_hits
        active_car_pairs = current_pairs

        # Usuwanie obiektów poza ekranem
        cars = [car for car in cars if 0 <= car.x <= WIDTH and 0 <= car.y <= HEIGHT]
        pedestrians = [ped for ped in pedestrians if 0 <= ped.x <= WIDTH and 0 <= ped.y <= HEIGHT]

        draw_intersection(WIN, light, cars, pedestrians, ped_collision_count, car_collision_count, elapsed_seconds)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
