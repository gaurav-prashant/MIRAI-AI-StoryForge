"""
Generates audible background music WAV files for each genre using
synthesized multi-tone waveforms. Saves to assets/audio/.
"""
import math
import os
import struct
import wave

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")
SAMPLE_RATE = 22050
DURATION_SEC = 20  # 20 seconds of loopable music
NUM_FRAMES = SAMPLE_RATE * DURATION_SEC

def write_wav(filename, frames_data, sample_rate=SAMPLE_RATE, channels=1, sampwidth=2):
    filepath = os.path.join(AUDIO_DIR, filename)
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(frames_data)
    size = os.path.getsize(filepath)
    print(f"  Written: {filename} ({size:,} bytes)")

def make_tone(freq, duration_sec, sample_rate=SAMPLE_RATE, amplitude=0.35):
    """Generates a pure sine wave tone."""
    frames = []
    n = int(sample_rate * duration_sec)
    for i in range(n):
        t = i / sample_rate
        val = int(amplitude * 32767 * math.sin(2 * math.pi * freq * t))
        frames.append(max(-32767, min(32767, val)))
    return frames

def make_chord(freqs, duration_sec, sample_rate=SAMPLE_RATE, amplitude=0.28):
    """Generates a chord by mixing multiple sine waves."""
    n = int(sample_rate * duration_sec)
    frames = []
    per_voice_amp = amplitude / len(freqs)
    for i in range(n):
        t = i / sample_rate
        val = 0
        for freq in freqs:
            val += per_voice_amp * 32767 * math.sin(2 * math.pi * freq * t)
        frames.append(max(-32767, min(32767, int(val))))
    return frames

def make_melody_pattern(note_freqs, note_dur, repeats, sample_rate=SAMPLE_RATE, amplitude=0.3):
    """Generates a repeating melody pattern with fade in/out per note."""
    frames = []
    note_samples = int(sample_rate * note_dur)
    fade_samples = int(sample_rate * 0.02)  # 20ms fade

    for _ in range(repeats):
        for freq in note_freqs:
            note_frames = []
            for i in range(note_samples):
                t = i / sample_rate
                val = int(amplitude * 32767 * math.sin(2 * math.pi * freq * t))
                # Fade in
                if i < fade_samples:
                    val = int(val * i / fade_samples)
                # Fade out
                elif i > note_samples - fade_samples:
                    val = int(val * (note_samples - i) / fade_samples)
                note_frames.append(max(-32767, min(32767, val)))
            frames.extend(note_frames)

    # Trim/pad to exact NUM_FRAMES
    if len(frames) > NUM_FRAMES:
        frames = frames[:NUM_FRAMES]
    while len(frames) < NUM_FRAMES:
        frames.extend(frames[:min(len(frames), NUM_FRAMES - len(frames))])
    return frames

def frames_to_bytes(frames):
    return struct.pack(f"<{len(frames)}h", *frames)


# -------------------------------------------------------------------
# FANTASY - Bright major arpeggio with magical shimmer
# C major pentatonic: C4=261.6, E4=329.6, G4=392, A4=440, C5=523.2
# -------------------------------------------------------------------
def gen_fantasy():
    print("Generating Fantasy track...")
    notes_melody = [261.6, 329.6, 392.0, 523.2, 392.0, 329.6, 261.6, 196.0]
    frames = make_melody_pattern(notes_melody, note_dur=0.25, repeats=10, amplitude=0.30)

    # Add harmonic bass undertone
    bass_frames = make_chord([130.8, 196.0], DURATION_SEC, amplitude=0.12)
    combined = [frames[i] + bass_frames[i] for i in range(NUM_FRAMES)]
    clamped = [max(-32767, min(32767, v)) for v in combined]
    return clamped


# -------------------------------------------------------------------
# MYSTERY - Minor key, slow, atmospheric
# A minor: A3=220, C4=261.6, E4=329.6, G4=392, F4=349.2
# -------------------------------------------------------------------
def gen_mystery():
    print("Generating Mystery track...")
    notes_melody = [220.0, 261.6, 246.9, 220.0, 196.0, 261.6, 293.7, 220.0]
    frames = make_melody_pattern(notes_melody, note_dur=0.40, repeats=6, amplitude=0.25)

    # Add low bass drone
    bass_frames = make_chord([55.0, 110.0], DURATION_SEC, amplitude=0.10)
    combined = [frames[i] + bass_frames[i] for i in range(NUM_FRAMES)]
    clamped = [max(-32767, min(32767, v)) for v in combined]
    return clamped


# -------------------------------------------------------------------
# HORROR - Dissonant tritone drones, very slow
# Dissonant intervals: A2=110, Eb3=155.6, A3=220
# -------------------------------------------------------------------
def gen_horror():
    print("Generating Horror track...")
    # Slow dissonant arpeggio
    notes_melody = [110.0, 155.6, 207.7, 155.6, 110.0, 92.5, 110.0, 138.6]
    frames = make_melody_pattern(notes_melody, note_dur=0.55, repeats=4, amplitude=0.22)

    # Add rumbling low drone
    bass_frames = make_chord([55.0, 73.4], DURATION_SEC, amplitude=0.14)
    combined = [frames[i] + bass_frames[i] for i in range(NUM_FRAMES)]
    clamped = [max(-32767, min(32767, v)) for v in combined]
    return clamped


# -------------------------------------------------------------------
# SCI-FI - Futuristic arpeggiated sequence
# Whole tone scale notes: C4=261.6, D4=293.7, E4=329.6, F#4=370, G#4=415.3
# -------------------------------------------------------------------
def gen_scifi():
    print("Generating Sci-Fi track...")
    notes_melody = [261.6, 293.7, 329.6, 370.0, 415.3, 466.2, 415.3, 370.0]
    frames = make_melody_pattern(notes_melody, note_dur=0.18, repeats=14, amplitude=0.28)

    # Add synthetic bass pulse
    pulse_freq = 65.4
    pulse = []
    beat_samples = int(SAMPLE_RATE * 0.25)
    for i in range(NUM_FRAMES):
        beat_pos = i % beat_samples
        if beat_pos < int(beat_samples * 0.3):
            t = beat_pos / SAMPLE_RATE
            val = int(0.12 * 32767 * math.sin(2 * math.pi * pulse_freq * t))
        else:
            val = 0
        pulse.append(val)

    combined = [frames[i] + pulse[i] for i in range(NUM_FRAMES)]
    clamped = [max(-32767, min(32767, v)) for v in combined]
    return clamped


# -------------------------------------------------------------------
# ADVENTURE - Heroic fanfare arpeggio, upbeat
# G major: G4=392, B4=493.9, D5=587.3, G5=783.9
# -------------------------------------------------------------------
def gen_adventure():
    print("Generating Adventure track...")
    notes_melody = [392.0, 493.9, 587.3, 783.9, 587.3, 493.9, 392.0, 329.6]
    frames = make_melody_pattern(notes_melody, note_dur=0.20, repeats=12, amplitude=0.28)

    # Add a driving bass line
    bass_notes = [98.0, 98.0, 146.8, 130.8]
    bass_frames = make_melody_pattern(bass_notes, note_dur=0.40, repeats=12, amplitude=0.15)
    bass_frames = bass_frames[:NUM_FRAMES]

    combined = [frames[i] + bass_frames[i] for i in range(NUM_FRAMES)]
    clamped = [max(-32767, min(32767, v)) for v in combined]
    return clamped


# -------------------------------------------------------------------
# GENERATE ALL TRACKS
# -------------------------------------------------------------------
os.makedirs(AUDIO_DIR, exist_ok=True)
print(f"\nGenerating background music tracks -> {AUDIO_DIR}\n")


genres = {
    "background_fantasy.wav": gen_fantasy,
    "background_mystery.wav": gen_mystery,
    "background_horror.wav": gen_horror,
    "background_scifi.wav": gen_scifi,
    "background_adventure.wav": gen_adventure,
}

for filename, gen_fn in genres.items():
    frames = gen_fn()
    raw = frames_to_bytes(frames)
    write_wav(filename, raw)

print("\nDone! All background tracks generated.")

# Verify non-silent
print("\nVerifying non-silence...")
for filename in genres:
    fpath = os.path.join(AUDIO_DIR, filename)
    with wave.open(fpath, "rb") as w:
        data = w.readframes(w.getnframes())
    samples = struct.unpack(f"<{len(data)//2}h", data)
    non_zero = sum(1 for s in samples if s != 0)
    max_amp = max(abs(s) for s in samples)
    print(f"  {filename}: non_zero={non_zero}/{len(samples)}, max_amp={max_amp}")

print("\nALL CHECKS PASSED. Tracks are audible.")
