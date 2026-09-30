import io
import math
import struct
import wave
import random
import pygame

class SoundManager:
    """Synthesizes retro 8-bit sound effects in-memory using standard library wave module."""
    def __init__(self):
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._create_sounds()
        except Exception as e:
            print(f"Audio init warning: {e}")

    def _generate_wav(self, kind):
        sr = 44100
        duration = 0.12 if kind == 'laser' else (0.25 if kind == 'explosion' else 0.5)
        n_samples = int(sr * duration)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            frames = bytearray()
            for i in range(n_samples):
                t = i / sr
                p = i / n_samples
                if kind == 'laser':
                    # Descending frequency sweep
                    freq = 900 * (1 - p * 0.6)
                    val = math.sin(2 * math.pi * freq * t)
                elif kind == 'explosion':
                    # White noise with fast initial decay
                    val = (random.random() * 2 - 1)
                else:  # game_over
                    # Low pitched descending drone
                    freq = 300 * (1 - p * 0.5)
                    val = math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(4 * math.pi * freq * t)
                
                env = (1 - p) ** 1.5
                s = int(val * env * 0.35 * 32767)
                s = max(-32768, min(32767, s))
                frames.extend(struct.pack('<h', s))
            w.writeframes(frames)
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def _create_sounds(self):
        try:
            self.sounds['laser'] = self._generate_wav('laser')
            self.sounds['explosion'] = self._generate_wav('explosion')
            self.sounds['game_over'] = self._generate_wav('game_over')
        except Exception as e:
            print(f"Sound generation warning: {e}")

    def play(self, name):
        try:
            if name in self.sounds:
                self.sounds[name].play()
        except Exception:
            pass
