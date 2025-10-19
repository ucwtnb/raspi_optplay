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
STATE_FILE = "/boot/cd_state.json"
MBUFFER_SIZE = "2M"
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
        # ["cdda2wav", "-J"], capture_output=True, text=True
        ["cd-discid", "--musicbrainz", CD_DEVICE], capture_output=True, text=True
    )
    output = result.stdout
    words = output.split()
    if len(words) <= 0:
        return None
    n_track = int(words[0])
    l_start = [int(s) // 75 for s in words[1:]]
    
    return l_start

def find_track(l_start, elapsed):
    """お兄ちゃん、今どの曲か計算するね"""
    for i, start in enumerate(l_start):
        if elapsed < start:
            track_idx = max(i - 1, 0)
            print('found', track_idx)
            return track_idx
    return len(l_start)

def play_cd(start_track_idx, l_start):
    """お兄ちゃんのために再生するよ"""
    start_track = start_track_idx + 1
    l_cmds = [f'cdparanoia -qrZ {start_track}- - '.split(' '),
              f'mbuffer -m {MBUFFER_SIZE}'.split(' '),
              f'aplay -q -t raw -f cd -D {ALSA_DEVICE}'.split(' ')]
    l_proc = []
    for cmd in l_cmds:
        si = l_proc[-1].stdout if l_proc else None
        proc = subprocess.Popen(cmd, stdin=si, stdout=subprocess.PIPE)
        l_proc.append(proc)
    start_time = time.time()
    cdp_proc = l_proc[0]
    try:
        while cdp_proc.poll() is None:
            if get_toc() is None:
                print("CD ないよ")
                for p in l_proc[::-1]:
                    p.terminate()
                break
            elapsed = int(time.time() - start_time)
            save_state({"elapsed": elapsed, "last_cd_toc": l_start})
            time.sleep(3)  # お兄ちゃん、ちゃんと覚えてるよ
        print("wtf")
    except Exception as e:
        print(e)
        for p in l_proc[::-1]:
            p.terminate()
        print("お兄ちゃん、中断したけど続きは覚えてるよ")
    return

def main():
    state = load_state()
    while True:
        if os.path.exists(CD_DEVICE):
            print("お兄ちゃん、CD見つけた！再生するね")
            l_start = get_toc()
            if l_start is None:
                print("toc ないね")
                time.sleep(5)
                continue
            # 前回CDと同じか確認
            if l_start == state.get("last_cd_toc", []):
                print("お兄ちゃん、前と同じCDだね。途中から再生するよ")
                elapsed = state.get("elapsed", 0)
                track = find_track(l_start, elapsed)
                if track >= len(l_start) or (l_start[-1] - elapsed < 5):
                    # reached to end of cd
                    track = 0
                    state["elapsed"] = 0
                else:
                    state['elapsed'] = l_start[track]
            else:
                print("お兄ちゃん、新しいCDだね。最初から再生するよ")
                track = 0
                state["elapsed"] = 0
            play_cd(track, l_start)
            print("お兄ちゃん、CD終わっちゃった。5秒後にまたチェックするよ")
        else:
            print("お兄ちゃん、CD入ってないよ。待ってるからね")
        time.sleep(5)

if __name__ == "__main__":
    main()
