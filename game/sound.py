from settings import *
from support import audio_importer
from states.gameplay import Gameplay, GameOver


class Sound:
    def __init__(self, game):
        self.game = game
        self.music = audio_importer(join('sounds', 'music'))
        self.prev_state = None
        self.state = Gameplay.music_state
        self.current_music = None

    def play_music(self):
        if self.state != self.prev_state:
            if self.current_music:
                self.current_music.fadeout(1000)
            if self.state == Gameplay.music_state:
                self.current_music = self.music.get('gameplay')
                if self.current_music:
                    self.current_music.set_volume(self.game.music_volume)
                    self.current_music.play(loops=-1)

    def update(self, dt):
        self.play_music()
        self.prev_state = self.state
        self.state = self.game.current_state.music_state
        for music in self.music.values():
            music.set_volume(self.game.music_volume)
