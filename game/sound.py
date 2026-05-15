from settings import *
from support import audio_importer, sound_importer


class Sound:
    def __init__(self, game):
        self.game = game
        self.music = audio_importer(join('sounds', 'music'))
        self.sounds = sound_importer('sounds')        # pistol_shot, etc. (только верхний уровень)
        self.step_sounds = list(audio_importer(join('sounds', 'steps')).values())
        self.prev_state = None
        self.state = 'main_menu'
        self.current_music = None

    def play_music(self):
        if self.state != self.prev_state:
            if self.current_music:
                self.current_music.fadeout(1000)
            music_map = {'gameplay': 'gameplay', 'shop': 'shop', 'main_menu': 'menu', 'settings': 'menu'}
            key = music_map.get(self.state)
            if key and key in self.music:
                self.current_music = self.music[key]
                self.current_music.set_volume(self.game.music_volume)
                self.current_music.play(loops=-1)

    def update(self, dt):
        self.play_music()
        self.prev_state = self.state
        self.state = self.game.current_state.music_state
        for music in self.music.values():
            music.set_volume(self.game.music_volume)
        for sound in self.sounds.values():
            sound.set_volume(self.game.sounds_volume)
        for sound in self.step_sounds:
            sound.set_volume(self.game.sounds_volume)
