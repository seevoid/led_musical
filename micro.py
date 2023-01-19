import pyaudio
import wave
import numpy
import math
import time
import struct
from scipy.signal import butter, lfilter, freqz
import csv

form_1 = pyaudio.paInt16 # 16-bit resolution
chans = 1 # 1 channel
samp_rate = 44100 # 44.1kHz sampling rate
# samp_rate = 49000
# chunk = 512 # 2^12 samples for buffer
chunk = 1024 
record_secs = 10 # seconds to record
dev_index = 2 # device index found by p.get_device_info_by_index(ii)
wav_output_filename = 'test1.wav' # name of .wav file

audio = pyaudio.PyAudio() # create pyaudio instantiation

# create pyaudio stream
stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                    input_device_index = dev_index,input = True, \
                    frames_per_buffer=chunk)
print("recording")
frames = []

0

power = 6
max = 0
min = 500000000000

SHORT_NORMALIZE = (1.0/32768.0)

doubles = None

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


cutoff_bass = 200 
cutoff_high = 300
power = 6

csv_file = open('./records.csv', 'w')
writer = csv.writer(csv_file)
header = ['bass', 'medium']
writer.writerow(header)

# loop through stream and append audio chunks to frame array
for ii in range(0,int(samp_rate/chunk*record_secs)):
# while True:
    data = stream.read(chunk, exception_on_overflow = False)
    data = numpy.fromstring(data, dtype=numpy.int16)
    
    # Get the Bass
    y_bass = butter_lowpass_filter(data, cutoff_bass, samp_rate, 2)
    AMP_BASS = int(numpy.average(numpy.abs(y_bass))*2)

    # Get Others
    y_high = butter_highpass_filter(data, cutoff_high, samp_rate, 2)
    AMP = int(numpy.average(numpy.abs(y_high))*2)

    print( str(AMP_BASS) + " | " + str(AMP))

    # writer.writerow([str(AMP_BASS), str(AMP)])


csv_file.close()

# stop the stream, close it, and terminate the pyaudio instantiation
stream.stop_stream()
stream.close()
audio.terminate()

FORMAT = pyaudio.paInt16

waveFile = wave.open("recording.wav", 'wb')
waveFile.setnchannels(chans)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(samp_rate)
waveFile.writeframes(b''.join(frames))
waveFile.close()
