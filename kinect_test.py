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


# Kinext initilization

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

BOARD_X, BOARD_Y = 90, 50
CASE_WIDTH = 230

def drawGrid(canvas, board):
    for x in range(Board.size):
        for y in range(Board.size):
            canvas.create_rectangle(x * CASE_WIDTH + BOARD_X, y * CASE_WIDTH + BOARD_Y,CASE_WIDTH,CASE_WIDTH, width=5)

fig = None
img = None

dmap_prev = None

#tkinter interface
screen_w, screen_h = 1024, 768
screen_dx, screen_dy = 1680, 0
canvas_w, canvas_h = screen_w - 220, screen_h - 150
canvas_dx, canvas_dy = 150, 180
# Create window
root = tk.Tk()
root.geometry("%dx%d+%d+%d" % (screen_w, screen_h, screen_dx, screen_dy))
root.bind("<Escape>", lambda e : (e.widget.withdraw(), e.widget.quit()))
canvas = None
# Fix canvas to window
canvas = tk.Canvas(root, width=canvas_w, height=canvas_h)
canvas.place(x=canvas_dx, y=canvas_dy)
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

    # dmap = gaussian_filter(dmap, sigma=7)
    norm = colors.Normalize(vmin=3340, vmax=3470)
    colorized_dmap = pl.cm.ScalarMappable(norm=norm).to_rgba(dmap)
    image = Image.fromarray(np.uint8(colorized_dmap*255))
    image = image.resize((canvas_w, canvas_h), Image.ANTIALIAS)
    rgbImage = ImageTk.PhotoImage('RGB', image.size)
    rgbImage.paste(image)    
    canvas.create_image(0, 0, anchor=tk.NW, image=rgbImage)
    drawGrid(canvas, None)
    canvas.place(x=canvas_dx, y=canvas_dy)
    root.update()

    listener.release(frames)

device.stop()
device.close()

sys.exit(0)
