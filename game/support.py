from settings import *
import json
import os
import time


class Timer:
    def __init__(self, duration, repeat=False, autostart=False, func=None):
        self.duration = duration
        self.start_time = 0
        self.active = False
        self.repeat = repeat
        self.func = func
        if autostart:
            self.activate()

    def __bool__(self):
        return self.active

    def activate(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.start_time = 0
        if self.repeat:
            self.activate()

    def update(self):
        if self.active:
            if pygame.time.get_ticks() - self.start_time >= self.duration:
                if self.func and self.start_time != 0:
                    self.func()
                self.deactivate()


def audio_importer(*path):
    audio_dict = {}
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in file_names:
            audio_dict[file_name.split('.')[0]] = pygame.mixer.Sound(join(folder_path, file_name))
    return audio_dict


def sound_importer(*path):
    """Загружает звуки только из верхнего уровня директории (нерекурсивно)."""
    import os
    result = {}
    dir_path = join(*path)
    if os.path.exists(dir_path):
        for file_name in os.listdir(dir_path):
            full = join(dir_path, file_name)
            if os.path.isfile(full):
                name = file_name.split('.')[0]
                result[name] = pygame.mixer.Sound(full)
    return result


def folder_importer(*path):
    surfs = {}
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            surfs[file_name.split('.')[0]] = pygame.image.load(full_path).convert_alpha()
    return surfs


def load_json(filepath) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_total_score(kills, waves):
    return kills * 2 + waves * 10


def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def create_score_json():
    path = join('settings', 'score.json')
    if not os.path.exists(path):
        write_json(path, {})


def write_score(kills, waves, total):
    path = join('settings', 'score.json')
    stats = {'kills': kills, 'waves': waves, 'total': total}
    score = load_json(path)
    if score:
        best_scores = list(score.values())
        best_scores.append(stats)
        best_scores.sort(reverse=True, key=lambda x: x['total'])
        if len(best_scores) > 10:
            del best_scores[-1]
    else:
        best_scores = [stats]
    write_json(path, {key: value for key, value in enumerate(best_scores, start=1)})


def transition_effect(surface, callback, fade_speed=20, hold_time=0.3, draw_callback=None):
    clock = pygame.time.Clock()
    fade_overlay = pygame.Surface(surface.get_size()).convert_alpha()
    for alpha in range(0, 256, fade_speed):
        if draw_callback:
            draw_callback()
        fade_overlay.fill((0, 0, 0, alpha))
        surface.blit(fade_overlay, (0, 0))
        pygame.display.update()
        clock.tick(60)
    callback()
    fade_overlay.fill((0, 0, 0, 255))
    surface.blit(fade_overlay, (0, 0))
    pygame.display.update()
    start = time.time()
    while time.time() - start < hold_time:
        clock.tick(60)
    for alpha in range(255, -1, -fade_speed):
        if draw_callback:
            draw_callback()
        fade_overlay.fill((0, 0, 0, alpha))
        surface.blit(fade_overlay, (0, 0))
        pygame.display.update()
        clock.tick(60)
