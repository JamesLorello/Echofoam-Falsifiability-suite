import argparse
import hashlib
import os
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw

try:
    from moviepy.editor import (
        VideoFileClip,
        TextClip,
        concatenate_videoclips,
        ImageClip,
        CompositeAudioClip,
    )
    from moviepy.audio.AudioClip import AudioArrayClip
    MOVIEPY_AVAILABLE = True
except Exception:
    MOVIEPY_AVAILABLE = False


def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def read_primes(path):
    primes = []
    with open(path) as f:
        for line in f:
            try:
                primes.append(float(line.strip()))
            except ValueError:
                pass
    return primes


def generate_resonance_audio(primes, duration, fps=44100):
    if not primes:
        return None
    segment = duration / len(primes)
    total_samples = int(duration * fps)
    audio = np.zeros(total_samples)
    idx = 0
    for p in primes:
        t = np.linspace(0, segment, int(segment * fps), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * p * t)
        end = idx + tone.size
        if end > audio.size:
            end = audio.size
            tone = tone[:end - idx]
        audio[idx:end] = tone
        idx = end
    return np.stack([audio, audio], axis=1)


def annotate_image(image_array, events, output_path):
    im = Image.fromarray(image_array)
    draw = ImageDraw.Draw(im)
    r = 10
    for x, y in events:
        draw.ellipse((x - r, y - r, x + r, y + r), outline='red', width=3)
    im.save(output_path)
    return np.array(im)


def main():
    parser = argparse.ArgumentParser(description='Create annotated mashup from simulation outputs.')
    parser.add_argument('simulation', help='simulation.mp4 file or folder of frames')
    parser.add_argument('epcd_results', help='epcd_results.txt file')
    parser.add_argument('collapse_events', help='collapse_events.txt file with x y per line')
    parser.add_argument('donna_prompt', help='text file with Donna-style prompt')
    parser.add_argument('primes', help='file with prime resonance values')
    args = parser.parse_args()

    primes = read_primes(args.primes)

    # metadata hashes
    hashes = {
        'simulation': hash_file(args.simulation) if os.path.isfile(args.simulation) else 'dir',
        'epcd_results': hash_file(args.epcd_results),
        'collapse_events': hash_file(args.collapse_events),
        'donna_prompt': hash_file(args.donna_prompt),
        'primes': hash_file(args.primes)
    }

    with open(args.donna_prompt) as f:
        prompt_text = f.read().strip()

    events = []
    with open(args.collapse_events) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    x, y = float(parts[-2]), float(parts[-1])
                    events.append((x, y))
                except ValueError:
                    continue

    if os.path.isfile(args.simulation) and MOVIEPY_AVAILABLE:
        clip = VideoFileClip(args.simulation)
        # intro frame
        intro = TextClip(prompt_text, fontsize=24, color='white', bg_color='black', size=clip.size).set_duration(3)
        # annotate final frame
        final_frame = clip.get_frame(clip.duration)
        annotated = annotate_image(final_frame, events, 'final_frame_annotated.png')
        end_clip = ImageClip(annotated).set_duration(3)
        # resonance audio
        resonance = generate_resonance_audio(primes, clip.duration)
        if resonance is not None:
            res_audio = AudioArrayClip(resonance, fps=44100)
            new_audio = clip.audio.set_duration(clip.duration).audio_fadein(0)
            clip = clip.set_audio(CompositeAudioClip([new_audio, res_audio]))
        final = concatenate_videoclips([intro, clip, end_clip])
        final.write_videofile('mashup.mp4', codec='libx264', audio_codec='aac')
    else:
        # handle frame directory only for annotation
        if os.path.isdir(args.simulation):
            frames = sorted(os.listdir(args.simulation))
            last_frame_path = os.path.join(args.simulation, frames[-1])
            image_array = np.array(Image.open(last_frame_path))
            annotate_image(image_array, events, 'final_frame_annotated.png')
        else:
            raise RuntimeError('Moviepy not available and simulation is not a directory of frames')
        print('No video processing performed (moviepy not available).')

    # metadata log
    resonance_score = sum(primes)
    with open('mashup_log.txt', 'w') as log:
        log.write(f'Time: {datetime.utcnow().isoformat()}\n')
        for k, v in hashes.items():
            log.write(f'{k}_hash: {v}\n')
        log.write(f'Resonance_score: {resonance_score}\n')
        log.write(f'Prompt: {prompt_text}\n')

    if not os.path.exists('mashup.mp4'):
        # create placeholder using final_frame if no video
        if os.path.exists('final_frame_annotated.png') and MOVIEPY_AVAILABLE:
            img = ImageClip('final_frame_annotated.png').set_duration(5)
            img.write_videofile('mashup.mp4', codec='libx264')

if __name__ == '__main__':
    main()
