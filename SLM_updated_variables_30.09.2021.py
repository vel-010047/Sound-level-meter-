#Modules 
import pyaudio
import math
import time
import tkinter.font as tkFont
from tkinter import *
import globalVars as gv
width = 500           # Width of the canvas
height = 200          # Height of the canvas

sample_rate = 44100        # Sample rate of the soundcard
update_speed = 1.1          # Update speed=1.1 sec

gate_time = [0.2, 0.5, 1.0, 2.0, 5.0, 10.0] # Gate Time list in seconds
gate_time_index = 1                         # index 1 from gate_time  as initial value i.e 0.5 sec

# UI Colors 
frames = "#000080"     
canvas = "#DBF3FA"
text = "#000000"
audio_bar = "#606060"
audio_loop = "#00ff00"
audio_max = "#ff0000"

# UI fonts
RMS_fontsize = 52           # Size of RMS value text 
INFO_fontsize = 8            # Size of info text

# UI Button sizes
Buttonwidth1 = 12
Buttonwidth2 = 10

audio_signal1 = []           # Audio trace channel 1    
audio_devin= None           # Audio device for input
audio_devout = None          # Audio device for output

run_state = 1               # 0 stop, 1 start
audio_state = 1             # 0 audio off, 1 audio on

RMS_ch1 = 0.0                # RMS value channel 1

audio_level = 0.0            # Maximum value of CH1

# ===================================Start and Stop widgets ========================================
   
def start(): 
    global run_state
    
    if (run_state == 0):
        run_state = 1

    screen_update()         # UpdateScreen()

def stop():
    global run_state
    
    if (run_state == 1):
        run_state = 0
    elif (run_state == 2):
        run_state = 3
    elif (run_state == 4):
        run_state = 3

    screen_update()         # UpdateScreen()
# ============================================ Main routine ====================================================
    
def audio_input():   # Read the audio from the stream and store the data into the arrays
    global audio_signal1
    global audio_devin
    global audio_devout
    global run_state
    global audio_state
    global gate_time
    global gate_time_index
    global sample_rate
    global update_speed
     
    while (True):                                           # Main loop
        PA = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16                            # Audio format 16-bit resolution
        CHUNK = int( float(sample_rate) * gate_time[gate_time_index])
        # run_state = 1 : Open Stream
        if (run_state == 1):
            if update_speed < 1:
                update_speed = 1.0
            if update_speed > 5:
                update_speed = 5.0

            TRACESopened = 1

            try:
                chunk_buffer = int(update_speed * CHUNK)

                if chunk_buffer < sample_rate / 10:           
                    chunk_buffer = int(sample_rate / 10)

                stream = PA.open(format = FORMAT,
                    channels = TRACESopened, 
                    rate = sample_rate, 
                    input = True,
                    output = True,
                    frames_per_buffer = int(chunk_buffer),
                    input_device_index = audio_devin,
                    output_device_index = audio_devout)
                run_state = 2
            except:                                         #  show error,if error in opening audio stream,
                run_state = 0
            screen_update()                               # screen_updatecall        
        # run_state = 2: Reading audio data from soundcard
        if (run_state == 2):
            signals = []
            try:
                signals = stream.read(chunk_buffer)          # Read samples from the buffer
            except:
                run_state = 4

            if (audio_state == 1):                          # Audio on 
                stream.write(signals, chunk_buffer)

            # Start conversion audio samples to values -32762 to +32767 (one's complement)
            signal_length = len(signals)                         # Lenght of signals array
            audio_signal1 = []                               # Clear the audio_signal1 array for trace 1

            Sbuffer = signal_length / 2                          # Sbuffer is number of values (2 bytes per audio sample value, 1 channel is 2 bytes)
            i = 2 * int(Sbuffer - CHUNK)                    # Start value, first part is skipped due to possible distortions

            if i < 0:                                       # Prevent negative values of i
                i = 0
                
            s = signal_length - 1       
            while (i < s):
                v = (signals[i]) + 256 *(signals[i+1])
                if v > 32767:                               # One's complement correction
                    v = v - 65535
                audio_signal1.append(v)                      # Append the value to the trace 1 array 
                i = i + 2                                   # 2 bytes per sample value and 1 trace is 2 bytes totally

            update_all()                                     # Update Data, trace and screen

        if (run_state == 3) or (run_state == 4):         # run_state = 3: Stop   # run_state = 4: Stop and restart

            stream.stop_stream()
            stream.close()
            PA.terminate()
            if run_state == 3:
                run_state = 0                               # Status is stopped 
            if run_state == 4:          
                run_state = 1                               # Status is start

            screen_update()                                 # Update screen with text  
        root.update_idletasks()
        root.update()                                       # Activate updated screens 

def update_all():        # Update Data, trace and screen
    calculate_RMS()      # RMS calculation
    screen_update()     # Update screen with text

def screen_update():     # Update screen with text
    display()        # Update the text
    root.update()       # Activate updated screens    

def calculate_RMS():                 # Calculate the RMS on channel 1
    global audio_signal1
    global sample_rate
    global RMS_ch1                   # The RMSvalue
    global audio_level               # Maximum value
    
    trace_size = len(audio_signal1)   # Set the trace length
    if trace_size == 0:
        return()

    # Zero offset correction routine only for trace 1
    AD1 = 0
    t = 0
    
    Vmin = 0
    Vmax = 0
    while t < trace_size:
        V = audio_signal1[t]
        AD1 = AD1 + V
        if V > Vmax:
            Vmax = V
        if V < Vmin:
            Vmin = V
        t = t + 1

    Vmin = -1 * Vmin        # Delete the minus sign

    audio_level = float(Vmin)
    if Vmax > audio_level:
        audio_level = float(Vmax)

    audio_level = audio_level / 32000
    if audio_level > 1.0:
        audio_level = 1.0            
    
    AD1 = int(AD1 /  trace_size)      

    # RMS calculation, only for trace 1
    RMS_ch1 = 0.0

    t = 0
    while t < trace_size:
        v1 = audio_signal1[t] - AD1
        RMS_ch1 = RMS_ch1 + v1 * v1
        t = t + 1

    RMS_ch1 = math.sqrt(RMS_ch1 / trace_size) # RMSvalue in steps of the AD converter
       
def display():                       # Update the screen with text
    global audio_signal1
    global run_state
    global audio_state
    global gate_time
    global gate_time_index
    global sample_rate
    global audio_level                   # Maximum audio value
    global RMS_ch1
    global RMSfont
    global INFOfont
    global audio_bar
    global audio_loop 
    global audio_max
    global width
    global height

    # Delete all items on the screen
    de = ca.find_enclosed ( 0, 0, width+1000, height+1000)   
    for n in de: 
        ca.delete(n)

    # RMS value printing
    if RMS_ch1 > 0.000001:                                     # Prevent log(0)
        txt = str(20 * math.log10(RMS_ch1)) + "000000"
        txt = txt[:2] + " dB"
    else:
        txt = "No signal"
    
    txt1 = "(SPL)"

    x = 100
    y = height / 2
    idTXT = ca.create_text(x, y, text=txt, font=RMSfont, anchor=W, fill=text)
    idTXT1 = ca.create_text(300, 110, text=txt1, font=RMSfont2, anchor=W, fill=text)
    
def select_audiodevice():        # Select an audio device
    global audio_devin
    global audio_devout
    py_audio = pyaudio.PyAudio()
    ndev = py_audio.get_device_count()
    n = 0
    ai = ""
    ao = ""
    while n < ndev:
        s = py_audio.get_device_info_by_index(n) #list of audio devices connected
        print( n, s)
        if s['maxInputChannels'] > 0:
            ai = ai + str(s['index']) + ": " + s['name'] + "\n"
        if s['maxOutputChannels'] > 0:
            ao = ao + str(s['index']) + ": " + s['name'] + "\n"
        n = n + 1
    py_audio.terminate()
    audio_devin= None #select default device for audio in
    audio_devout = None#select default device for audio out

def exit_app():
    root.destroy()    
# ================ Make Screen ==========================

root=Tk()
root.title("Noise level meter (dB)")

root.minsize(100, 100)

frame1 = Frame(root, background=frames, borderwidth=5, relief=RIDGE)
frame1.pack(side=TOP, expand=1, fill=X)

frame2 = Frame(root, background="black", borderwidth=5, relief=RIDGE)
frame2.pack(side=TOP, expand=1, fill=X)

frame3 = Frame(root, background=canvas, borderwidth=5, relief=RIDGE)
frame3.pack(side=TOP, expand=1, fill=X)

ca = Canvas(frame2, width=width, height=height, background=canvas)
ca.pack(side=TOP)


b = Button(frame3, text="Start", width=Buttonwidth2, bg=gv.NAVY_BLUE,fg=gv.WHITE,activebackground =gv.ORANGE,activeforeground=gv.WHITE ,command=start)
b.pack(side=LEFT, padx=25, pady=5)

b = Button(frame3, text="Stop", width=Buttonwidth2, bg=gv.NAVY_BLUE,fg=gv.WHITE, activebackground =gv.ORANGE,activeforeground=gv.WHITE,command=stop)
b.pack(side=LEFT, padx=25, pady=5)

b = Button(frame3, text="Exit", width=Buttonwidth2, bg=gv.NAVY_BLUE,fg=gv.WHITE, activebackground =gv.ORANGE,activeforeground=gv.WHITE,command=exit_app)
b.pack(side=LEFT, padx=25, pady=5)

# Fonts initialisation of the tk screen 
RMSfont = tkFont.Font(size=RMS_fontsize)
RMSfont2 = tkFont.Font(size=20)
RMSfont3 = tkFont.Font(size=30)
INFOfont = tkFont.Font(size=INFO_fontsize)

# ================ Call main===============================
#root.update()
root.update_idletasks()

select_audiodevice()
audio_input()