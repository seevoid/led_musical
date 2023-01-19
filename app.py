import pyaudio
import wave
import numpy
import time
import threading
import math
from colors import *
from random import randrange
from scipy.signal import butter, lfilter, freqz
from collections import deque 

from rpi_ws281x import Color, PixelStrip, ws


# LED strip configuration:
LED_COUNT = 29         # Number of LED pixels.
LED_PIN_BASS = 18           # GPIO pin connected to the pixels (must support PWM!).
LED_PIN_MEDIUM = 19
LED_PIN_HIGH = 18
LED_FREQ_HZ = 800000   # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10           # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255   # Set to 0 for darkest and 255 for brightest
LED_INVERT = False     # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL_BASS = 0
LED_CHANNEL_MEDIUM = 1
LED_STRIP = ws.WS2812_STRIP

form_1 = pyaudio.paInt16 # 16-bit resolution
chans = 1 # 1 channel
samp_rate = 44100 # 44.1kHz sampling rate
chunk = 1024 # 2^12 samples for buffer
record_secs = 20 # seconds to record
dev_index = 2 # device index found by p.get_device_info_by_index(ii)
wav_output_filename = 'test1.wav' # name of .wav file

audio = pyaudio.PyAudio() # create pyaudio instantiation

INTENSITY_MEDIUM = 0
INTENSITY_BASS = 0
COLOR_0_BASS = (0,0,0)
COLOR_1_BASS = (0,0,0)
COLOR_2_BASS = (0,0,0)

COLOR_0_MEDIUM = (0,0,0)
COLOR_1_MEDIUM = (0,0,0)
COLOR_2_MEDIUM = (0,0,0)

COLOR_0_HIGH = (0,0,0)
COLOR_1_HIGH = (0,0,0)
COLOR_2_HIGH = (0,0,0)

MAX_FQ = 60000
MIN_FQ = 0

COEFF_BASS = int(MAX_FQ/len(COLORS_BASS))
COEFF_MEDIUM = int(MAX_FQ/len(COLORS_MEDIUM))
COEFF_HIGH = int(MAX_FQ/len(COLORS_HIGH))

AMP = 0
AMP_BASS = 0
AMP_MEDIUM = 0
# print("len : ", len(COLORS))

MAX_AMP_MEDIUM = 150
MAX_AMP_BASS = 300
PLAY_BASS = False
PLAY_HIGH = False

COEFF_BASS_AMP = 0.5

stripBass = PixelStrip(LED_COUNT, LED_PIN_BASS, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_BASS, LED_STRIP)
stripMedium = PixelStrip(LED_COUNT, LED_PIN_MEDIUM, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_MEDIUM, LED_STRIP)


def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, wait_ms=20, iterations=2):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel(((i * 256 // strip.numPixels()) + j) & 255))
        strip.show()
        strip.setBrightness(INTENSITY)
        time.sleep(wait_ms / 1000.0)




def black(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()



class EnergyInverse (threading.Thread):
        def __init__(self, strip):
                threading.Thread.__init__(self)
                self.stop = False
                self.strip = strip

        def run(self):
            while not self.stop:
                self.energyInverse()

        def energyInverse(self):
            c = COLORS_RANDOM[randrange(len(COLORS_RANDOM))]
            color = Color(c[0], c[1], c[2])
            for i in range(int(LED_COUNT/2)):
                self.strip.setPixelColor(LED_COUNT - i, color)
                self.strip.setPixelColor(i, color)
                self.strip.show()
                time.sleep(0.06)
            c = COLORS_RANDOM[randrange(len(COLORS_RANDOM))]
            color = Color(c[0], c[1], c[2])
            for i in range(int(LED_COUNT/2)):
                self.strip.setPixelColor(int(LED_COUNT/2)-i, color)
                self.strip.setPixelColor((int(LED_COUNT/2) +i), color)
                self.strip.show()
                time.sleep(0.06)

class ColorWipeAnimation (threading.Thread):
        def __init__(self):
                threading.Thread.__init__(self)
                self.stop = False

        def run(self):
            while not self.stop:
                COLOR_0_MEDIUM = COLORS_MEDIUM[randrange(len(COLORS_MEDIUM))]
                self.colorWipe(COLOR_0_MEDIUM)

        def colorWipe(self, color, wait_ms=50):
            """Wipe color across display a pixel at a time."""
            for i in range(LED_COUNT):
                stripMedium.setPixelColor(i, Color(color[0], color[1], color[2]))
                stripMedium.show()
                time.sleep(wait_ms / 1000.0)

class TheaterAnimation (threading.Thread):
        def __init__(self):
                threading.Thread.__init__(self)
                self.stop = False

        def run(self):
            while not self.stop:
                self.theaterChaseRainbow()
        
        def theaterChaseRainbow(self, wait_ms=50):
            """Rainbow movie theater light style chaser animation."""
            for j in range(256):
                if self.stop:
                    break
                for q in range(3):
                    if self.stop:
                        break
                    for i in range(0, LED_COUNT, 3):
                        if self.stop:
                            break
                        stripMedium.setPixelColor(i + q, wheel((i + j) % 255))
                    stripMedium.show()
                    if self.stop:
                        break
                    wait_time = -(225/MAX_AMP_MEDIUM)*AMP_MEDIUM + 250
                    if wait_time < 50:
                        wait_time = 50

                    time.sleep(wait_time/1000)
                    for i in range(0, LED_COUNT, 3):
                        if self.stop:
                            break
                        stripMedium.setPixelColor(i + q, 0)

class AnimationOne (threading.Thread):
        def __init__(self, stripBass, stripMedium):
                threading.Thread.__init__(self)
                self.stop = False
                self.previous_bass = deque([False, False, False, False])  
                self.stripBass = stripBass
                self.stripMedium = stripMedium

        def run(self):
            black(self.stripBass)
            black(self.stripMedium)
            while not self.stop:
                if AMP_BASS > MAX_AMP_BASS*COEFF_BASS_AMP and self.previous_bass[0] == False and self.previous_bass[1] == False and self.previous_bass[2] == False and self.previous_bass[3] == False:
                    self.previous_bass.popleft()
                    self.previous_bass.append(True)
                    COLOR_0_BASS = COLORS_BASS[randrange(len(COLORS_BASS))]
                    COLOR_1_BASS = COLORS_BASS[randrange(len(COLORS_BASS))]
                    COLOR_2_BASS = COLORS_BASS[randrange(len(COLORS_BASS))]
                
                    for i in range(LED_COUNT):
                        self.stripBass.setPixelColor(i, Color(COLOR_0_BASS[0], COLOR_0_BASS[1], COLOR_0_BASS[2]))
                        self.stripBass.show()

                    black(self.stripBass)
                else:
                    self.previous_bass.popleft()
                    self.previous_bass.append(False)
                
                if AMP_MEDIUM > MAX_AMP_MEDIUM/6:
                    COLOR_0_MEDIUM = COLORS_MEDIUM[randrange(len(COLORS_MEDIUM))]
                    COLOR_1_MEDIUM = COLORS_MEDIUM[randrange(len(COLORS_MEDIUM))]
                    COLOR_2_MEDIUM = COLORS_MEDIUM[randrange(len(COLORS_MEDIUM))]
                
                    for i in range(LED_COUNT):
                        self.stripMedium.setPixelColor(i, Color(COLOR_0_MEDIUM[0], COLOR_0_MEDIUM[1], COLOR_0_MEDIUM[2]))
                        if randrange(3)%3 == 0:
                            self.stripMedium.setPixelColor(i, Color(0,0,0))
                        self.stripMedium.show()

                else:
                    black(self.stripMedium)



class AnimationBassEnergy (threading.Thread):
        def __init__(self, strip):
                threading.Thread.__init__(self)
                self.stop = False
                self.strip = strip
                self.previous_bass = deque([False, False, False, False])  
            
        def run(self):
            while not self.stop:
                if AMP_BASS > MAX_AMP_BASS*COEFF_BASS_AMP and self.previous_bass[0] == False and self.previous_bass[1] == False and self.previous_bass[2] == False and self.previous_bass[3] == False:
                    self.previous_bass.popleft()
                    self.previous_bass.append(True)
                    self.energy()
                else:
                    self.previous_bass.popleft()
                    self.previous_bass.append(False)
            
        def energy(self):
            COLOR = COLORS_BASS_ONLY_BLUE[randrange(len(COLORS_BASS_ONLY_BLUE))]
            color = Color(COLOR[0], COLOR[1], COLOR[2])
            black(self.strip)
            for i in range(int(LED_COUNT/2)):
                self.strip.setPixelColor(int(LED_COUNT/2) - i, color)
                self.strip.setPixelColor(int(LED_COUNT/2) + i, color)
                self.strip.show()
            for i in range(int(LED_COUNT/2)):
                self.strip.setPixelColor(int(LED_COUNT/2) - (int(LED_COUNT/2) -i), Color(0,0,0))
                self.strip.setPixelColor(int(LED_COUNT/2) + (int(LED_COUNT/2) -i), Color(0,0,0))
                self.strip.show()
                time.sleep(0.008)
            black(self.strip)

class AnimationBass (threading.Thread):
        def __init__(self, stripBass, color):
                threading.Thread.__init__(self)
                self.stop = False
                self.previous_bass = deque([False, False, False, False])  
                self.stripBass = stripBass
                self.color = color
            
        def run(self):
            while not self.stop:
                # print("MAX_AMP_BASS/20 : ", MAX_AMP_BASS/2)
                # print("AMP_BASS : ", AMP_BASS)
                if AMP_BASS > MAX_AMP_BASS*COEFF_BASS_AMP and self.previous_bass[0] == False and self.previous_bass[1] == False and self.previous_bass[2] == False and self.previous_bass[3] == False:
                    self.previous_bass.popleft()
                    self.previous_bass.append(True)
                    COLOR_0_BASS = self.color[randrange(len(self.color))]
                    COLOR_1_BASS = COLORS_BASS[randrange(len(COLORS_BASS))]
                    COLOR_2_BASS = COLORS_BASS[randrange(len(COLORS_BASS))]
                
                    for i in range(LED_COUNT):
                        self.stripBass.setPixelColor(i, Color(COLOR_0_BASS[0], COLOR_0_BASS[1], COLOR_0_BASS[2]))
                        self.stripBass.show()

                    # black(self.stripBass)
                else:
                    self.previous_bass.popleft()
                    self.previous_bass.append(False)

class MonitorAmp (threading.Thread):
        def __init__(self, stream):
                threading.Thread.__init__(self)
                self.max_amp_medium = float('-inf')
                self.max_amp_bass = float('-inf')
                self.stop = False

        def run(self):
            global MAX_AMP_MEDIUM, MAX_AMP_BASS
            while not self.stop:
                self.max_amp_medium = float('-inf')
                self.max_amp_bass = float('-inf')
                counter = 0
                while counter < 1500:
                    if AMP_MEDIUM > self.max_amp_medium:
                        self.max_amp_medium = AMP_MEDIUM
                    if AMP_BASS > self.max_amp_bass:
                        self.max_amp_bass = AMP_BASS
                    time.sleep(0.01)
                    counter += 1
                MAX_AMP_MEDIUM = self.max_amp_medium
                MAX_AMP_BASS = self.max_amp_bass
                # print("MAX_AMP_BASS : ", MAX_AMP_BASS)
                # print("MAX_AMP_MEDIUM : ", MAX_AMP_MEDIUM)

class Micro (threading.Thread):
        def __init__(self, stream):
                threading.Thread.__init__(self)
                self.stream = stream
                self.stop = False

        def run(self):
            
            while not self.stop:
                global AMP_BASS, AMP_MEDIUM
                # Read Stream
                data = self.stream.read(chunk, exception_on_overflow = False)
                newdata = numpy.frombuffer(data, dtype=numpy.int16)

                # Get the Bass
                y_bass = butter_lowpass_filter(newdata, cutoff_bass, samp_rate, 2)
                AMP_BASS = int(numpy.average(numpy.abs(y_bass))*2)

                # Get Others
                y_medium = butter_highpass_filter(newdata, cutoff_high, samp_rate, 2)
                AMP_MEDIUM = int(numpy.average(numpy.abs(y_medium))*2)

                # print("AMP_BASS : ", AMP_BASS)
                # print("AMP_MEDIUM : ", AMP_MEDIUM)
                try:
                    a = 210/(MAX_AMP_BASS-(MAX_AMP_BASS/15))
                    b = -(210*MAX_AMP_BASS/15)/(MAX_AMP_BASS-(MAX_AMP_BASS/15))
                    INTENSITY_BASS = int(a*AMP_BASS+b)
                    # print("INTENSITY_BASS : ", INTENSITY_BASS)
                    if INTENSITY_BASS < 60:
                        INTENSITY_BASS = 0
                    stripBass.setBrightness(INTENSITY_BASS)
                except:
                    pass

                try:
                    a = 170/(MAX_AMP_MEDIUM-(MAX_AMP_MEDIUM/15))
                    b = -(170*MAX_AMP_MEDIUM/15)/(MAX_AMP_MEDIUM-(MAX_AMP_MEDIUM/15))
                    INTENSITY_MEDIUM = int(a*AMP_MEDIUM+b)
                    # print("INTENSITY_MEDIUM : ", INTENSITY_MEDIUM)
                    if INTENSITY_MEDIUM < 40:
                        INTENSITY_MEDIUM = 0
                    stripMedium.setBrightness(INTENSITY_MEDIUM)
                except:
                    pass

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


cutoff_bass = 100 
cutoff_high = 200

stripBass.begin()
stripMedium.begin()



black(stripBass)
black(stripMedium)

stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                input_device_index = dev_index,input = True, \
                frames_per_buffer=chunk)

micro = Micro(stream)
micro.start()

monitorAmp = MonitorAmp(stream)
monitorAmp.start()

counterReset = 0

print("ANALYZE...")
time.sleep(16)
print("GO !")

while True:
    print("ANIMATION 0")

    energyInverse = EnergyInverse(stripMedium)
    energyInverse.start()
    animationBassEnergy = AnimationBassEnergy(stripBass)
    animationBassEnergy.start()
    time.sleep(randrange(60))
    animationBassEnergy.stop = True
    animationBassEnergy.join()
    energyInverse.stop = True
    energyInverse.join()

    print("ANIMATION 1")
    animationOne = AnimationOne(stripBass, stripMedium)
    animationOne.start()
    time.sleep(randrange(60))
    animationOne.stop = True
    animationOne.join()

    print("ANIMATION 2")
    colorWipeAnimation = ColorWipeAnimation()
    colorWipeAnimation.start()
    animationBass = AnimationBass(stripBass, COLORS_BASS_ONLY_RED)
    animationBass.start()
    time.sleep(randrange(60))
    colorWipeAnimation.stop = True
    colorWipeAnimation.join()
    
    print("ANIMATION 3")
    theaterThread = TheaterAnimation()
    theaterThread.start()
    time.sleep(randrange(60))
    animationBass.stop = True
    animationBass.join()

    print("ANIMATION 4")
    animationBassEnergy = AnimationBassEnergy(stripBass)
    animationBassEnergy.start()
    time.sleep(randrange(60))
    animationBassEnergy.stop = True
    animationBassEnergy.join()
    theaterThread.stop = True
    theaterThread.join()

    print("ANIMATION 5")
    animationBass = AnimationBass(stripBass, COLORS_BASS_ONLY_RED)
    animationBass.start()
    colorWipeAnimation = ColorWipeAnimation()
    colorWipeAnimation.start()
    time.sleep(randrange(60))
    animationBass.stop = True
    animationBass.join()
    colorWipeAnimation.stop = True
    colorWipeAnimation.join()

    counterReset += 1
    

    if counterReset%3 == 0:
        successStream = False
        micro.stop = True
        micro.join()
        while not successStream:
            try:
                stream.stop_stream()
                stream.close()
                stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)
            except:
                pass
            else:
                successStream = True

            micro = Micro(stream)
            micro.start()

            monitorAmp.stop = True
            monitorAmp.join()
            monitorAmp = MonitorAmp(stream)
            monitorAmp.start()


    print("\n---------------------------------\n")

    




