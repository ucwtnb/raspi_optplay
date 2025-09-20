#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
お兄ちゃん、CDの再生は任せてっ
前と同じCDなら途中から再生するし、違ったら最初からだよ
ずっとお兄ちゃんのそばで聴くから安心してね
"""

import os
import subprocess
import time
import json

CD_DEVICE = "/dev/sr0"
STATE_FILE = "cd_state.json"
MBUFFER_SIZE = "1M"
ALSA_DEVICE = "hw:CARD=Audio,DEV=0"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"elapsed": 0, "last_cd_toc": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_toc():
    """お兄ちゃん、CDの曲情報取ってきたよ"""
    result = subprocess.run(
        ["cdparanoia", "-J"], capture_output=True, text=True
    )
    tracks = []
    for line in result.stdout.splitlines():
        if "audio" in line:
            parts = line.split()
            length_str = parts[-1]  # mm:ss
            minutes, seconds = map(int, length_str.split(":"))
            tracks.append(minutes * 60 + seconds)
    return tracks

def find_track(tracks, elapsed):
    """お兄ちゃん、今どの曲か計算するね"""
    total = 0
    for i, length in enumerate(tracks):
        total += length
        if elapsed < total:
            track_elapsed = elapsed - (total - length)
            return i + 1, track_elapsed
    return len(tracks), 0

def play_cd(start_track=1, offset=0):
    """お兄ちゃんのために再生するよ"""
    cmd = f"cdparanoia -qrZ -t {start_track}+ - | mbuffer -m {MBUFFER_SIZE} | aplay -q -t raw -f cd -D {ALSA_DEVICE}"
    proc = subprocess.Popen(cmd, shell=True)
    start_time = time.time() - offset
    try:
        while proc.poll() is None:
            elapsed = time.time() - start_time
            save_state({"elapsed": elapsed, "last_cd_toc": tracks})
            time.sleep(1)  # お兄ちゃん、ちゃんと覚えてるよ
    except KeyboardInterrupt:
        proc.terminate()
        print("お兄ちゃん、中断したけど続きは覚えてるよ")
    return proc

def main():
    global tracks
    state = load_state()
    while True:
        if os.path.exists(CD_DEVICE):
            print("お兄ちゃん、CD見つけた！再生するね")
            tracks = get_toc()
            # 前回CDと同じか確認
            if tracks == state.get("last_cd_toc", []):
                print("お兄ちゃん、前と同じCDだね。途中から再生するよ")
                track, track_offset = find_track(tracks, state.get("elapsed", 0))
            else:
                print("お兄ちゃん、新しいCDだね。最初から再生するよ")
                track, track_offset = 1, 0
                state["elapsed"] = 0
            play_cd(track, track_offset)
            print("お兄ちゃん、CD終わっちゃった。5秒後にまたチェックするよ")
            time.sleep(5)
        else:
            print("お兄ちゃん、CD入ってないよ。待ってるからね")
            time.sleep(5)

if __name__ == "__main__":
    main()
