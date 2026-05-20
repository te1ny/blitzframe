from settings import *


class Button(pygame.sprite.Sprite):
    def __init__(self, groups, pos, text='', font=None, size=(200, 50),
                 bg_color='white', text_color='black', callback='', image=None):
        super().__init__(groups)
        self._prev_pressed = False
        self.was_hovered = False
        self.callback = callback
        self.custom_image = image

        if self.custom_image:
            self.image = self.custom_image.copy()
        else:
            self.image = pygame.Surface(size)
            self.image.fill(bg_color)
            if font and text:
                txt = font.render(text, True, text_color)
                self.image.blit(txt, txt.get_rect(center=(size[0] // 2, size[1] // 2)))

        self.rect = self.image.get_rect(center=pos)
        self.hover_sound = pygame.mixer.Sound(join('sounds', 'hover.mp3'))
        self.click_sound = pygame.mixer.Sound(join('sounds', 'click.mp3'))

    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        just = pressed and not self._prev_pressed
        self._prev_pressed = pressed
        if self.rect.collidepoint(mouse_pos) and just:
            self.click_sound.play()
            return True
        return False

    def hover(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            if not self.was_hovered:
                self.hover_sound.play()
            self.was_hovered = True
            if self.custom_image:
                self.image = self.custom_image.copy()
                overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                pygame.draw.ellipse(overlay, (100, 100, 100, 30), overlay.get_rect())
                self.image.blit(overlay, (0, 0))
        else:
            if self.custom_image:
                self.image = self.custom_image.copy()
            self.was_hovered = False

    def update(self, dt):
        super().update()
        self.hover()


class Slider(pygame.sprite.Sprite):
    def __init__(self, groups, pos, size=(200, 10),
                 min_value=0.0, max_value=1.0, initial_value=0.5,
                 color_bg='#cccccc', color_fg='#CA7842', handle_color='#4B352A',
                 label_text='', label_font=None, label_color='white'):
        super().__init__(groups)
        self.width, self.height = size
        self.min_value, self.max_value = min_value, max_value
        self.value = initial_value
        self.color_bg, self.color_fg, self.handle_color = color_bg, color_fg, handle_color
        self.dragging = False

        self.label_surf = None
        label_width = label_height = 0
        if label_text and label_font:
            self.label_surf = label_font.render(label_text, True, label_color)
            label_width = self.label_surf.get_width() + 10
            label_height = self.label_surf.get_height()

        self.label_width = label_width
        self.total_height = max(self.height, label_height) + 10
        self.image = pygame.Surface((self.width + label_width + 20, self.total_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.update_slider()

    def update_slider(self):
        self.image.fill((0, 0, 0, 0))
        slider_y = (self.total_height - self.height) // 2
        if self.label_surf:
            self.image.blit(self.label_surf, (0, (self.total_height - self.label_surf.get_height()) // 2))
        progress_width = int((self.value - self.min_value) / (self.max_value - self.min_value) * self.width)
        pygame.draw.rect(self.image, self.color_bg, (self.label_width, slider_y, self.width, self.height), border_radius=5)
        pygame.draw.rect(self.image, self.color_fg, (self.label_width, slider_y, progress_width, self.height), border_radius=5)
        pygame.draw.circle(self.image, self.handle_color, (self.label_width + progress_width, slider_y + self.height // 2), 10)

    def get_value(self):
        return self.value

    def input(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if self.dragging and not mouse_pressed[0]:
            self.dragging = False
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            self.dragging = True
        if self.dragging:
            rel_x = max(0, min(self.width, mouse_pos[0] - self.rect.left - self.label_width))
            self.value = self.min_value + (rel_x / self.width) * (self.max_value - self.min_value)
            self.update_slider()

    def update(self, dt):
        self.input()


def draw_text_window(surface, pos, text, font=None, padding=14, bg_color=(50, 50, 50, 200), text_color=(220, 220, 220), border_radius=8):
    if not font:
        font = pygame.font.SysFont('monospace', 18)
    lines = text.split('\n')
    line_surfs = [font.render(ln, True, text_color) for ln in lines]
    w = max(s.get_width() for s in line_surfs) + padding * 2
    lh = line_surfs[0].get_height() if line_surfs else 20
    h = lh * len(line_surfs) + padding * 2
    window_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(window_surf, bg_color, window_surf.get_rect(), border_radius=border_radius)
    for i, s in enumerate(line_surfs):
        window_surf.blit(s, (padding, padding + i * lh))
    x = pos[0] - w - 10
    y = pos[1] - h // 2
    surface.blit(window_surf, (x, y))
