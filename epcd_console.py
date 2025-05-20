
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import os

def load_audio(file_path, target_sr=100):
    sr, audio = wavfile.read(file_path)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)  # convert to mono
    duration = len(audio) / sr
    target_len = int(target_sr * duration)
    audio_resampled = signal.resample(audio, target_len)
    audio_normalized = (audio_resampled - np.min(audio_resampled)) / (np.max(audio_resampled) - np.min(audio_resampled)) * 0.2 + 0.05
    return audio_normalized, target_sr, duration

def detect_peaks(psi, sr):
    peaks, _ = signal.find_peaks(psi, distance=sr * 0.3)
    return peaks, np.diff(peaks) / sr

def compute_coherence(intervals):
    primes = np.array([2, 3, 5, 7, 11, 13, 17, 19, 23, 29])
    prime_diffs = np.diff(primes)
    coherence_primes = np.mean([any(np.isclose(i, primes, rtol=0.5)) for i in intervals]) if len(intervals) > 0 else 0
    coherence_diffs = np.mean([any(np.isclose(i, prime_diffs, rtol=0.5)) for i in intervals]) if len(intervals) > 0 else 0
    return max(coherence_primes, coherence_diffs)

def compute_decoherence(psi, peaks):
    decoherence = np.zeros_like(psi)
    for i in range(len(peaks) - 1):
        segment = psi[peaks[i]:peaks[i+1]]
        var = np.var(segment)
        decoherence[peaks[i]:peaks[i+1]] = var
    return decoherence / np.max(decoherence)

def generate_tone_file(tone_cues, duration, out_path="epcd_tone_output.wav", base_volume=0.5):
    sr = 44100
    audio = np.zeros(int(sr * duration))
    for time_s, freq in tone_cues:
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        tone = base_volume * np.sin(2 * np.pi * freq * t)
        start = int(time_s * sr)
        end = min(start + len(tone), len(audio))
        audio[start:end] += tone[:end - start]
    audio = np.int16(audio / np.max(np.abs(audio)) * 32767)
    wavfile.write(out_path, sr, audio)
    print(f"Tone file saved to: {out_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 epcd_console.py input.wav")
        return

    file_path = sys.argv[1]
    print(f"Loading: {file_path}")
    psi, sr, duration = load_audio(file_path)
    peaks, intervals = detect_peaks(psi, sr)
    coherence = compute_coherence(intervals)
    decoherence = compute_decoherence(psi, peaks)

    print(f"Coherence Score: {coherence:.2%}")

    threshold = 0.5
    prime_list = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    valley_indices = np.where(decoherence > threshold)[0]
    valley_times = valley_indices / sr
    valley_midpoints = []

    if len(valley_times) > 0:
        region = [valley_times[0]]
        for i in range(1, len(valley_times)):
            if valley_times[i] - valley_times[i-1] <= 0.1:
                region.append(valley_times[i])
            else:
                valley_midpoints.append(np.mean(region))
                region = [valley_times[i]]
        valley_midpoints.append(np.mean(region))

    tone_cues = [(t, 100 * prime_list[i % len(prime_list)]) for i, t in enumerate(valley_midpoints)]
    for t, f in tone_cues:
        print(f"Tone Cue: {t:.2f}s -> {f:.1f} Hz")

    generate_tone_file(tone_cues, duration)

    with open("epcd_results.txt", "w") as f:
        f.write(f"Input file: {file_path}\n")
        f.write(f"Coherence Score: {coherence:.2%}\n")
        for t, f0 in tone_cues:
            f.write(f"Tone Cue: {t:.2f}s -> {f0:.1f} Hz\n")
    print("Results saved to epcd_results.txt")

if __name__ == "__main__":
    main()
