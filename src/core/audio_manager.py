import pygame
import numpy as np
import os
from src.utilities.constants import get_resource_path


class AudioManager:
    _sounds = {}
    _master_volume = 0.3

    @classmethod
    def init_audio(cls):
        try:
            # --- NEW: Force the Pygame mixer to exactly match our Numpy array format! ---
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
        except Exception as e:
            print(f"Audio failed to initialize: {e}")
            return

        sound_files = {
            'click': 'click.wav',
            'reveal': 'reveal.wav',
            'flag': 'flag.wav',
            'explode': 'explode.wav',
            'win': 'win.wav'
        }

        loaded_count = 0
        for name, filename in sound_files.items():
            path = get_resource_path(os.path.join("sounds", filename))
            if os.path.exists(path):
                try:
                    cls._sounds[name] = pygame.mixer.Sound(path)
                    loaded_count += 1
                except pygame.error as e:
                    print(f"Error loading {filename}: {e}, using synthesized sound instead")
                    cls._sounds[name] = cls._synthesize_sound(name)
            else:
                cls._sounds[name] = cls._synthesize_sound(name)

        if loaded_count == 0:
            print("No audio files found - using synthesized minesweeper sounds")

    @classmethod
    def _synthesize_sound(cls, name, sample_rate=44100):  # Bumped to standard 44.1kHz
        if name == 'click':
            return cls._create_tone(800, 0.1, sample_rate, 'exponential')
        elif name == 'reveal':
            return cls._create_tone(1000, 0.15, sample_rate, 'exponential')
        elif name == 'flag':
            return cls._create_tone(1200, 0.12, sample_rate, 'exponential')
        elif name == 'explode':
            return cls._create_noise(0.5, sample_rate, 'exponential')
        elif name == 'win':
            return cls._create_chord([523, 659, 784, 1047], 0.2, sample_rate)
        return None

    @classmethod
    def _create_tone(cls, frequency, duration, sample_rate=44100, envelope='exponential'):
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        wave = np.sin(2 * np.pi * frequency * t)
        fade = np.exp(-3 * t / duration) if envelope == 'exponential' else np.linspace(1, 0, num_samples)
        wave = np.int16(wave * fade * cls._master_volume * 32767)
        stereo = np.zeros((num_samples, 2), dtype=np.int16)
        stereo[:, 0] = stereo[:, 1] = wave

        # Pygame-CE handles Numpy arrays perfectly using the 'array' parameter
        return pygame.mixer.Sound(array=stereo)

    @classmethod
    def _create_noise(cls, duration, sample_rate=44100, envelope='exponential'):
        num_samples = int(sample_rate * duration)
        noise = np.random.uniform(-1, 1, num_samples)
        fade = np.exp(
            -5 * np.linspace(0, duration, num_samples) / duration) if envelope == 'exponential' else np.linspace(1, 0,
                                                                                                                 num_samples)
        noise = np.int16(noise * fade * cls._master_volume * 32767)
        stereo = np.zeros((num_samples, 2), dtype=np.int16)
        stereo[:, 0] = stereo[:, 1] = noise
        return pygame.mixer.Sound(array=stereo)

    @classmethod
    def _create_chord(cls, frequencies, note_duration, sample_rate=44100):
        total_duration = note_duration * len(frequencies) * 0.75
        num_samples = int(sample_rate * total_duration)
        combined = np.zeros((num_samples, 2), dtype=np.int16)
        for i, freq in enumerate(frequencies):
            start = int(i * note_duration * 0.75 * sample_rate)
            n = int(note_duration * sample_rate)
            t = np.linspace(0, note_duration, n)
            wave = np.int16(np.sin(2 * np.pi * freq * t) * np.exp(-3 * t / note_duration) * cls._master_volume * 32767)
            end = min(start + n, num_samples)
            combined[start:end, 0] += wave[:end - start]
            combined[start:end, 1] += wave[:end - start]
        combined = np.clip(combined, -32768, 32767)
        return pygame.mixer.Sound(array=combined)

    @classmethod
    def set_volume(cls, volume):
        cls._master_volume = max(0.0, min(1.0, volume))
        for sound in cls._sounds.values():
            if sound:
                sound.set_volume(cls._master_volume)

    @classmethod
    def play(cls, name):
        if name in cls._sounds and cls._sounds[name]:
            cls._sounds[name].play()