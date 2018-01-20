# coding: utf-8

import numpy as np
import sys
import pylab as pl
from matplotlib import cm, colors
from scipy.ndimage.filters import gaussian_filter
import Tkinter as tk
from PIL import Image, ImageTk
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel
from ttt3 import Board

try:
    from pylibfreenect2 import OpenGLPacketPipeline
    pipeline = OpenGLPacketPipeline()
except:
    from pylibfreenect2 import CpuPacketPipeline
    pipeline = CpuPacketPipeline()


def initKinect():
    None 

def drawGrid(canvas, board):
    canvas.create_line(0,0,400,400, width=5)
    None



# Create and set logger
logger = createConsoleLogger(LoggerLevel.Debug)
setGlobalLogger(logger)

# Check that kinnect is connected
fn = Freenect2()
num_devices = fn.enumerateDevices()
if num_devices == 0:
    print("No device connected!")
    sys.exit(1)

serial = fn.getDeviceSerialNumber(0)
device = fn.openDevice(serial, pipeline=pipeline)

listener = SyncMultiFrameListener(FrameType.Ir | FrameType.Depth)

# Register listeners
device.setIrAndDepthFrameListener(listener)
device.start()


fig = None
img = None

dmap_prev = None

#tkinter interface
w, h = 1024, 768
dx, dy = 1680, 0
# Create window
root = tk.Tk()
root.geometry("%dx%d+%d+%d" % (w, h, dx, dy))
root.bind("<Escape>", lambda e : (e.widget.withdraw(), e.widget.quit()))
canvas = None
# Fix canvas to window
canvas = tk.Canvas(root, width=w, height=h)
canvas.pack()
canvas.configure(background="red")

while True:
    frames = listener.waitForNewFrame()

    depth = frames["depth"]

    # depth is measured in millimeters and stored as a 512x424 float32 array
    dmap = depth.asarray()
    dmap = np.clip(4500 - dmap, 0, 4500)
    dmap = dmap[:,::-1]

    if img is None:
        img = pl.imshow(dmap, vmin=3340, vmax=3470)
    else:
        img.set_data(dmap)

    dmap = gaussian_filter(dmap, sigma=7)
    norm = colors.Normalize(vmin=3340, vmax=3470)
    colorized_dmap = pl.cm.ScalarMappable(norm=norm).to_rgba(dmap)
    image = Image.fromarray(np.uint8(colorized_dmap*255))
    rgbImage = ImageTk.PhotoImage('RGB', image.size)
    rgbImage.paste(image)    
    canvas.create_image(w/2, h/2, image=rgbImage)
    canvas.pack()
    root.update()

    listener.release(frames)

device.stop()
device.close()

sys.exit(0)
