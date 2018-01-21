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


# Kinect initialization

# Create and set logger
logger = createConsoleLogger(LoggerLevel.Debug)
setGlobalLogger(logger)

# Check that kinect is connected
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

KINECT_W, KINECT_H = 512, 424
BOARD_X, BOARD_Y = 80, 34
CASE_WIDTH = 100
BOARD_WIDTH = CASE_WIDTH * 3
MIN_HAND_HEIGHT = 3500

# Tkinter interface
screen_w, screen_h = 1024, 768
screen_dx, screen_dy = 1680, 0
canvas_w, canvas_h = screen_w - 265, screen_h - 155
canvas_dx, canvas_dy = 150, 180


def get_next_dmap():
    frames = listener.waitForNewFrame()

    depth = frames["depth"]

    # depth is measured in millimeters and stored as a 512x424 float32 array
    depth_map = depth.asarray()
    depth_map = np.clip(4500 - depth_map, 0, 4500)

    return frames, depth_map[:, ::-1]


def map_scale(x, y):
    return x * (canvas_w / float(KINECT_W)), y * (canvas_h / float(KINECT_H))


def draw_grid(canvas, board):
    O_X, O_Y = map_scale(BOARD_X, BOARD_Y)
    o_x, o_y = O_X, O_Y
    case_w_in_canvas, __ = map_scale(CASE_WIDTH, 0)
    for x in range(Board.size):
        for y in range(Board.size):
            canvas.create_rectangle(o_x, o_y, o_x + case_w_in_canvas, o_y + case_w_in_canvas, width=5)
            canvas.create_text(o_x + case_w_in_canvas/2, o_y + case_w_in_canvas/2, text=board.grid[y][x])
            o_y += case_w_in_canvas
        o_x += case_w_in_canvas
        o_y = O_Y


def detect_hand(depth_map):
    #max, x, y = 0, 0, 0
    for i_h in xrange(0, len(depth_map), 10):
        for i_w in xrange(0, len(depth_map[i_h]), 10):
            if depth_map[i_h][i_w] > MIN_HAND_HEIGHT:
                return True
                #max = depth_map[i_h][i_w]
                #x, y = i_w, i_h
    #return max, x, y
    return False


def get_board_depth_map(depth_map):
    return depth_map[BOARD_Y:(BOARD_Y + BOARD_WIDTH), BOARD_X:(BOARD_X + BOARD_WIDTH)]


def get_dmap_case(x, y, board_depthmap):
    return board_depthmap[y*CASE_WIDTH: y*CASE_WIDTH + CASE_WIDTH, x*CASE_WIDTH: x*CASE_WIDTH+CASE_WIDTH]


def get_most_diff_case(snapshot_dmap, actual_dmap):
    diff_dmap = actual_dmap - snapshot_dmap
    max_diff, max_x, max_y = 0, 0, 0
    for x in range(Board.size):
        for y in range(Board.size):
            case_diff_map = get_dmap_case(x, y, diff_dmap)
            case_diff = np.median(np.abs(case_diff_map))
            print(x, y, case_diff)
            if case_diff > max_diff:
                max_diff = case_diff
                max_x, max_y = x, y

    return max_x, max_y


def reset_buf_dmap():
    return np.zeros((BOARD_WIDTH, BOARD_WIDTH))

t3_board = Board()

# Filling board for testing
for x in range(Board.size):
    for y in range(Board.size):
        t3_board.grid[y][x] = str(y * Board.size + x)


# Create window
root = tk.Tk()
root.geometry("%dx%d+%d+%d" % (screen_w, screen_h, screen_dx, screen_dy))
root.bind("<Escape>", lambda e : (e.widget.withdraw(), e.widget.quit()))
canvas = None
# Fix canvas to window
canvas = tk.Canvas(root, width=canvas_w, height=canvas_h)
canvas.place(x=canvas_dx, y=canvas_dy)
canvas.configure(background="red")

fig = None
img = None
isPlaying = False

buf_dmap = reset_buf_dmap()
NB_FRAME = 10

# Get initial depth map snapshot
for i in range(NB_FRAME):
    frames, dmap = get_next_dmap()
    listener.release(frames)
    buf_dmap += gaussian_filter(get_board_depth_map(dmap), sigma=1)
snapshot_dmap = buf_dmap
buf_dmap = reset_buf_dmap()


count = 0
while True:
    frames, dmap = get_next_dmap()

    # Crop depth map to keep only the board inbound
    board_dmap = get_board_depth_map(dmap)
    gauss_board = gaussian_filter(board_dmap, sigma=1)

    if detect_hand(gaussian_filter(board_dmap, sigma=7)):
        print('Hand')
        isPlaying = True
        count = 0
        buf_dmap = reset_buf_dmap()
    elif isPlaying and count < NB_FRAME:
        buf_dmap += gauss_board
        count += 1
    elif isPlaying and count == NB_FRAME:
        isPlaying = False
        print(get_most_diff_case(snapshot_dmap, buf_dmap))
        snapshot_dmap = buf_dmap

    norm = colors.Normalize(vmin=3340, vmax=3470)
    colorized_dmap = pl.cm.ScalarMappable(norm=norm).to_rgba(dmap)
    image = Image.fromarray(np.uint8(colorized_dmap*255))
    image = image.resize((canvas_w, canvas_h), Image.ANTIALIAS)
    rgbImage = ImageTk.PhotoImage('RGB', image.size)
    rgbImage.paste(image)
    canvas.create_image(0, 0, anchor=tk.NW, image=rgbImage)
    draw_grid(canvas, t3_board)
    canvas.place(x=canvas_dx, y=canvas_dy)
    root.update()
    listener.release(frames)

device.stop()
device.close()

sys.exit(0)
