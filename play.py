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


g_record_hw = 'hw:CARD=Rx,DEV=0'
g_l_play_hw = ['hw:CARD=Device,DEV=0', 'hw:CARD=Audio,DEV=0', 'hw:CARD=iD4,DEV=0']
g_hw_add_info = {'hw:CARD=iD4,DEV=0':{'bit':32, 'format':'S32_LE', 'channel':4}}

#arecord -f S16_LE -c 2 -r 44100 -D hw:CARD=Rx,DEV=0 | sox -t raw -r 44100 -e signed -b 16 -c 2 - -t raw -r 44100 -e signed -b 32 -c 4 - | aplay -f S32_LE -c 4 -r 44100 -D hw:CARD=iD4,DEV=0

def get_hw_connections():

    cmd = 'arecord', '-L'
    record_output = subprocess.check_output(cmd, encoding='utf-8')
    if not g_record_hw in record_output:
        print('no record device.')
        return None
    print('found', g_record_hw)

    cmd = 'aplay', '-L'
    play_output = subprocess.check_output(cmd, encoding='utf-8')
    play_hw = None
    for play_hw in g_l_play_hw:
        if play_hw in play_output:
            break
    if not play_hw:
        print('no play device.')
        return None
    print('found', play_hw)

    return g_record_hw, play_hw

def play(hw_info):
    assert hw_info is not None
    record_devname, play_devname = hw_info

    try:
        cmd = ['arecord', '-f', 'cd', '-D', record_devname]
        #cmd = ['arecord', '-f', 'S24_3LE', '-c', '2', '-r', '44100', '-D', record_devname]
        print(' '.join(cmd))
        arecord_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        prev_process = arecord_process

        if play_devname in g_hw_add_info:
            info = g_hw_add_info[play_devname]
            cmd =['sox', '-t', 'raw', '-r', '44100',
                  '-b', '16', '-e', 'signed', '-c', '2', '-',
                  '-t', 'raw', '-b', str(info['bit']), '-c', str(info['channel']), '-']
            #cmd = ['sox', '-t', 'raw', '-r', '44100', '-e', 'signed', '-b',
            #       '24', '-c', '2', '-', '-t', 'raw', '-r', '44100', 
            #       '-e', 'signed', '-b', '32', '-']
            sox_process = subprocess.Popen(
                cmd,
                stdin=prev_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            prev_process = sox_process
            print(' '.join(cmd))
        else:
            sox_process = None

        if play_devname in g_hw_add_info:
            info = g_hw_add_info[play_devname]
            cmd = ['aplay', '-f', str(info['format']),'-c', str(info['channel']), '-r', '44100',
                   '-D', play_devname]
        else:
            cmd = ['aplay', '-f', 'S16_LE','-c', '2', '-r', '44100',
                   '-D', play_devname]
        aplay_process = subprocess.Popen(
                cmd,
                stdin=prev_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        print(' '.join(cmd))

        arecord_process.stdout.close()
        arecord_process.wait()
        if sox_process is not None:
            sox_process.stdout.close()
            sox_process.wait()
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
