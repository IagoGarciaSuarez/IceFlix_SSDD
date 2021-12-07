#!/usr/bin/env python3
# pylint: disable=C0103

'''
RTSP implementation based on gstreamer and libVlc
'''

import shlex
import os.path
import logging
import subprocess

try:
    import vlc
except ImportError:
    logging.warning('python-vlc required for player!')


# pylint: disable=C0301
TEST_PIPE = 'videotestsrc ! x264enc ! h264parse config-interval=5 ! mpegtsmux ! rtpmp2tpay ! udpsink host={} port={}'
FILE_PIPE = 'filesrc location="{}" ! decodebin ! x264enc ! h264parse config-interval=5 ! mpegtsmux ! rtpmp2tpay ! udpsink host={} port={}'
# pylint: enable=C0301


class RTSPEmitter:
    '''Handling RTSP streaming to a given destination'''
    def __init__(self, media_file, dest_host, dest_port):
        self._host_ = dest_host
        self._port_ = dest_port
        if (media_file is None) or not os.path.exists(media_file):
            logging.warning('No media file found! Use test signal')
            self._pipe_ = TEST_PIPE.format(self._host_, self._port_)
        else:
            self._pipe_ = FILE_PIPE.format(media_file, self._host_, self._port_)
        logging.debug('GST Pipe: %s', self._pipe_)
        self._proc_ = None

    def start(self):
        '''Start streaming'''
        self._proc_ = subprocess.Popen(shlex.split('gst-launch-1.0 {}'.format(self._pipe_)))

    def stop(self):
        '''Stop streaming'''
        self._proc_.terminate()

    def wait(self):
        '''Wait until streaming process terminates'''
        self._proc_.wait()

    @property
    def playback_uri(self):
        '''Get playback URI'''
        return f'rtp://@{self._host_}:{self._port_}'


class RTSPPlayer:
    '''RTSP player using SDP file'''
    def __init__(self, debug_mode=False):
        self._vlc_ = vlc.Instance('--verbose 3' if debug_mode else '')
        self._player_ = self._vlc_.media_player_new()

    def play(self, media_uri):
        '''Start playing media URI (in a separated window)'''
        media = self._vlc_.media_new(media_uri)
        self._player_.set_media(media)
        self._player_.play()

    def stop(self):
        '''Stop player (kill window)'''
        self._player_.stop()


if __name__ == '__main__':
    ## Test code for this library ##
    import time
    import tempfile

    logging.basicConfig(level=logging.DEBUG)

    # Stream test signal (filename is None)
    #emitter = RTSPEmitter(<video file>, '127.0.0.1', 5000)
    emitter = RTSPEmitter('server_media/Mosca amarilla pica a pupo tonto.mp4', '127.0.0.1', 5000)
    emitter.start()

    # PLay SDP file with VLC
    player = RTSPPlayer()
    player.play(emitter.playback_uri)

    # Stream for 10 seconds
    time.sleep(10.0)

    # Stop player and streamer
    player.stop()
    emitter.stop()
