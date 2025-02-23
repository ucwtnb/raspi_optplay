# -*- coding:utf-8 -*_
import os, sys
import time
import subprocess

# check hw connections
# if got input an output
# run arecord and aplay
# if got error
# retry all
def main():

    while True:
        hw_info = hw_connection_loop()
        play(hw_info)
        print('retrying...')
        time.sleep(1)

def hw_connection_loop():
    while True:
        hw_info = get_hw_connections()
        if hw_info is not None:
            return hw_info
        time.sleep(1)

def get_hw_connections():

    record_hw = 'hw:CARD=Rx,DEV=0'
    l_play_hw = ['hw:CARD=Device,DEV=0', 'hw:CARD=Audio,DEV=0']

    cmd = 'arecord', '-L'
    record_output = subprocess.check_output(cmd, encoding='utf-8')
    if not record_hw in record_output:
        print('no record device.')
        return None
    print('found', record_hw)

    cmd = 'aplay', '-L'
    play_output = subprocess.check_output(cmd, encoding='utf-8')
    play_hw = None
    for play_hw in l_play_hw:
        if play_hw in play_output:
            break
    if not play_hw:
        print('no play device.')
        return None
    print('found', play_hw)

    return record_hw, play_hw

def play(hw_info):
    assert hw_info is not None
    record_devname, play_devname = hw_info

    try:
        cmd = ['arecord', '-f', 'cd', '-D', record_devname]
        print(' '.join(cmd))
        arecord_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        cmd = ['aplay', '-f', 'cd', '-D', play_devname]
        aplay_process = subprocess.Popen(
                cmd,
                stdin=arecord_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        print(' '.join(cmd))

        arecord_process.stdout.close()
        arecord_process.wait()
        aplay_process.wait()

        stdout_data, stderr_data = aplay_process.communicate()

        if stdout_data:
            print("Standard Output:")
            print(stdout_data.decode())

        if stderr_data:
            print("Standard Error:")
            print(stderr_data.decode())
    except Exception as e:
        raise e
        return

if __name__ == '__main__':
    main()
