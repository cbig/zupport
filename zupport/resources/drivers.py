#!/usr/bin/python
# coding=utf-8

import os

from zupport.utilities import APP_RESOURCES

# OSGeo OGR compliant driver names

drivers = {"ESRI Shapefile": "shp",
           "TIGER": "tr",
           "MapInfo File": "tab",
           "GML": "gml"}

class ZAudioPlayer(object):
    '''Generic utility class for playing WAV sounds.
    
    Instance of the class depends on PyAudio.'''
    
    def __init__(self):
        # If PyAudio import fails exception will be propagated 
        try:
            import pyaudio
            import wave
        except ImportError, e:
            raise ImportError('No PyAudio available sound support not enabled',  e)
        
        # Set the relevant directory and file associations
        soundsdir = os.path.join(APP_RESOURCES, 'sounds')
        self.sounds = {'error': os.path.join(soundsdir, 'Error1.wav')}
        
        self.player = pyaudio.PyAudio()
        self.open = wave.open
        
    def __del__(self):
        self.player.terminate()
    
    @property
    def error(self):
        self.play(self.sounds['error'])
    
    def play(self, inputwavefile, loop):
        chunk = 1024
        
        wavefile = self.open(inputwavefile, 'rb')
        
        # open stream
        stream = self.player.open(format =
                                  self.player.get_format_from_width(wavefile.getsampwidth()),
                                  channels = wavefile.getnchannels(),
                                  rate = wavefile.getframerate(),
                                  output = True)
        
        for i in range(0, loop):
            # read data
            data = wavefile.readframes(chunk)
            # play stream
            while data != '':
                stream.write(data)
                data = wavefile.readframes(chunk)
    
            wavefile.rewind()
            #time.sleep(1)
        stream.close()
        
if __name__ == '__main__':
    audio = ZAudioPlayer()
    audio.play(audio.sounds['error'], loop=5)
    