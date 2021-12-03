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
TEST_PIPE = 'videotestsrc ! openh264enc ! rtph264pay config-interval=10 pt=96 ! udpsink host={} port={}'
FILE_PIPE = 'filesrc location="{}" ! decodebin ! openh264enc ! rtph264pay config-interval=10 pt=96 ! udpsink host={} port={}'
SDP_DATA = '''v=0
m=video {} RTP/AVP 96
c=IN IP4 {}
a=rtpmap:96 H264/90000
'''
# pylint: enable=C0301


class RTSPEmitter:
    '''Handling RTSP streaming to a given destination'''
    def __init__(self, media_file, dest_host, dest_port):
        if (media_file is None) or not os.path.exists(media_file):
            logging.warning('No media file found! Use test signal')
            self._pipe_ = TEST_PIPE.format(dest_host, dest_port)
        else:
            self._pipe_ = FILE_PIPE.format(media_file, dest_host, dest_port)
        logging.debug('GST Pipe: %s', self._pipe_)
        self._sdp_ = SDP_DATA.format(dest_port, dest_host)
        logging.debug('SDP Data: %s', self._sdp_)
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
    def sdp(self):
        '''Get SDP data'''
        return self._sdp_


class RTSPPlayer:
    '''RTSP player using SDP file'''
    def __init__(self):
        self._vlc_ = vlc.Instance()
        self._player_ = self._vlc_.media_player_new()

    def play(self, sdp_file):
        '''Start playing SDP file (in a separated window)'''
        media = self._vlc_.media_new(sdp_file)
        media.get_mrl()
        self._player_.set_media(media)
        self._player_.play()

    def stop(self):
        '''Stop player (kill window)'''
        self._player_.stop()


if __name__ == '__main__':
    ## Test code for this library ##
    import time
    import tempfile

    # Stream test signal (filename is None)
    emitter = RTSPEmitter(None, '127.0.0.1', 60606)
    emitter.start()

    # Create temporal file with SDP data as contents
    # Extension should be ".sdp" to work with libVLC
    tmp_file = tempfile.NamedTemporaryFile(mode='wt', suffix='.sdp', delete=False)
    tmp_file.write(emitter.sdp)
    tmp_file.close()

    # PLay SDP file with VLC
    player = RTSPPlayer()
    player.play(tmp_file.name)

    # Stream for 10 seconds
    time.sleep(10.0)

    # Stop player and streamer
    player.stop()
    emitter.stop()

    # Remove unused SDP file
    os.remove(tmp_file.name)
