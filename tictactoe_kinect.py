# coding: utf-8
import numpy as np
import sys
import pylab as pl
from matplotlib import cm, colors
from scipy.ndimage.filters import gaussian_filter
import Tkinter as tk
import tkFont
from PIL import Image, ImageTk
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from tictactoe_board import Board

try:
    from pylibfreenect2 import OpenGLPacketPipeline
    pipeline = OpenGLPacketPipeline()
except:
    from pylibfreenect2 import CpuPacketPipeline
    pipeline = CpuPacketPipeline()


KINECT_W, KINECT_H = 512, 424
SCREEN_DX, SCREEN_DY = 1680, 0
SCREEN_W, SCREEN_H = 1024, 768
BOARD_X, BOARD_Y = 80, 34
DEFAULT_CANVAS_W, DEFAULT_CANVAS_H = SCREEN_W - 265, SCREEN_H - 155
DEFAULT_CANVAS_DX, DEFAULT_CANVAS_DY = 150, 180

CASE_WIDTH = 100
CASE_MARGIN_DETECT = CASE_WIDTH / 4
BOARD_WIDTH = CASE_WIDTH * 3
MOVE_STEP = 5
ZOOM_STEP = 5

MIN_HAND_HEIGHT = 3500
MIN_DIFF_ACCEPTED = 11
NB_FRAME = 10
NB_WAITING_FRAME = 10

# Display settings
BACKGROUND_COLOR = 'cyan'
MESSAGE_COLOR = 'white'
background = True

# Calibrate board position
canvas_w, canvas_h = DEFAULT_CANVAS_W, DEFAULT_CANVAS_H
canvas_dx, canvas_dy = DEFAULT_CANVAS_DX, DEFAULT_CANVAS_DY


def get_next_dmap():
    frames = listener.waitForNewFrame()

    depth = frames["depth"]

    # depth is measured in millimeters and stored as a 512x424 float32 array
    depth_map = depth.asarray()
    depth_map = np.clip(4500 - depth_map, 0, 4500)

    return frames, depth_map[:, ::-1]


def map_scale(x, y):
    return x * (canvas_w / float(KINECT_W)), y * (canvas_h / float(KINECT_H))


def draw_message(msg):
    global canvas
    O_X, O_Y = map_scale(BOARD_X, BOARD_Y)
    board_width_canvas, __ = map_scale(BOARD_WIDTH, 0)
    if msg is not None:
        canvas.create_text(O_X + board_width_canvas / 2, O_Y + board_width_canvas / 2,
                           text=msg, font=SYMBOL_FONT, fill=MESSAGE_COLOR, angle=180, justify=tk.CENTER)


def draw_current_player():
    global canvas, board
    O_X, O_Y = map_scale(BOARD_X, BOARD_Y)
    board_width_canvas, __ = map_scale(BOARD_WIDTH, 0)
    if not board.finished:
        canvas.create_text(O_X + board_width_canvas, O_Y + board_width_canvas + 10,
            text="Now playing: " + board.player, font=STATUS_FONT, fill=MESSAGE_COLOR, angle=180, anchor=tk.SW)


def draw_board():
    global canvas, board
    O_X, O_Y = map_scale(BOARD_X, BOARD_Y)
    o_x, o_y = O_X, O_Y
    case_w_in_canvas, __ = map_scale(CASE_WIDTH, 0)
    for x in range(Board.size):
        for y in range(Board.size):
            canvas.create_rectangle(o_x, o_y, o_x + case_w_in_canvas, o_y + case_w_in_canvas, width=5)
            fill_color = 'yellow' if (x, y) in board.winning_cases else 'black'
            canvas.create_text(o_x + case_w_in_canvas/2, o_y + case_w_in_canvas/2, text=board.grid[y][x], font=SYMBOL_FONT, fill=fill_color)
            o_y += case_w_in_canvas
        o_x += case_w_in_canvas
        o_y = O_Y


def draw_grid(msg):
    draw_board()
    draw_message(msg)
    draw_current_player()


def display_background():
    global canvas, background


def detect_hand(depth_map):
    for i_h in xrange(0, len(depth_map), 10):
        for i_w in xrange(0, len(depth_map[i_h]), 10):
            if depth_map[i_h][i_w] > MIN_HAND_HEIGHT:
                return True
    return False


def get_board_depth_map(depth_map):
    return depth_map[BOARD_Y:(BOARD_Y + BOARD_WIDTH), BOARD_X:(BOARD_X + BOARD_WIDTH)]


def get_dmap_case(x, y, board_depthmap):
    return board_depthmap[y * CASE_WIDTH + CASE_MARGIN_DETECT: y * CASE_WIDTH + CASE_WIDTH - CASE_MARGIN_DETECT,
           x * CASE_WIDTH + CASE_MARGIN_DETECT: x * CASE_WIDTH + CASE_WIDTH - CASE_MARGIN_DETECT]


def get_most_diff_case(snapshot_dmap, actual_dmap):
    diff_dmap = actual_dmap - snapshot_dmap
    max_diff, max_x, max_y = 0, 0, 0
    for x in range(Board.size):
        for y in range(Board.size):
            case_diff_map = get_dmap_case(x, y, diff_dmap)
            case_diff = np.median(np.abs(case_diff_map))
            if case_diff > max_diff:
                max_diff = case_diff
                max_x, max_y = x, y

    return max_x, max_y, max_diff


def reset_buf_dmap():
    return np.zeros((BOARD_WIDTH, BOARD_WIDTH))



def build_depth_rgb_image():
    norm = colors.Normalize(vmin=3340, vmax=3470)
    colorized_dmap = pl.cm.ScalarMappable(norm=norm).to_rgba(dmap)
    image = Image.fromarray(np.uint8(colorized_dmap * 255))
    image = image.resize((canvas_w, canvas_h), Image.ANTIALIAS)
    rgb_image = ImageTk.PhotoImage('RGB', image.size)
    rgb_image.paste(image)
    return rgb_image


def init_depth_snapshot():
    # Get initial depth map snapshot
    buf = reset_buf_dmap()
    for i in range(NB_FRAME):
        frames, dmap = get_next_dmap()
        listener.release(frames)
        buf += gaussian_filter(get_board_depth_map(dmap), sigma=1)
    return buf


def toggle_background(event):
    global background
    background = not background


def quit(event):
    global running
    running = False
    # e.widget.withdraw(), e.widget.quit()


def move_canvas_left(event):
    global canvas_dx
    canvas_dx += MOVE_STEP


def move_canvas_right(event):
    global canvas_dx
    canvas_dx -= MOVE_STEP


def move_canvas_up(event):
    global canvas_dy
    canvas_dy += MOVE_STEP


def move_canvas_down(event):
    global canvas_dy
    canvas_dy -= MOVE_STEP


def reset_canvas_pos(event):
    global canvas_dx, canvas_dy, canvas_h, canvas_w
    canvas_w, canvas_h = DEFAULT_CANVAS_W, DEFAULT_CANVAS_H
    canvas_dx, canvas_dy = DEFAULT_CANVAS_DX, DEFAULT_CANVAS_DY


def zoom_in_canvas(event):
    global canvas_w, canvas_h
    canvas_h += ZOOM_STEP
    canvas_w += ZOOM_STEP


def zoom_out_canvas(event):
    global canvas_w, canvas_h
    canvas_h -= ZOOM_STEP
    canvas_w -= ZOOM_STEP


# Kinect initialization
fn = Freenect2()
num_devices = fn.enumerateDevices()
if num_devices == 0:
    print("No device connected!")
    sys.exit(1)
serial = fn.getDeviceSerialNumber(0)
device = fn.openDevice(serial, pipeline=pipeline)
listener = SyncMultiFrameListener(FrameType.Ir | FrameType.Depth)
device.setIrAndDepthFrameListener(listener)
device.start()

# Create tKinter interface
root = tk.Tk()
root.geometry("%dx%d+%d+%d" % (SCREEN_W, SCREEN_H, SCREEN_DX, SCREEN_DY))
canvas = None
root.bind("<Escape>", quit)
root.bind("<b>", toggle_background)
root.bind("<Left>", move_canvas_left)
root.bind("<Right>", move_canvas_right)
root.bind("<Up>", move_canvas_up)
root.bind("<Down>", move_canvas_down)
root.bind("<KP_0>", reset_canvas_pos)
root.bind("<0>", reset_canvas_pos)
root.bind("<KP_Add>", zoom_in_canvas)
root.bind("<KP_Subtract>", zoom_out_canvas)
root.bind("<i>", zoom_in_canvas)
root.bind("<o>", zoom_out_canvas)
canvas = tk.Canvas(root, width=canvas_w, height=canvas_h)
canvas.place(x=canvas_dx, y=canvas_dy)
canvas.configure(background=BACKGROUND_COLOR)

SYMBOL_FONT = tkFont.Font(family="Helvetica", size=72, weight='bold')
STATUS_FONT = tkFont.Font(family="Helvetica", size=36, weight='bold')


# Global variables
running = True
board = Board()
snapshot_dmap = init_depth_snapshot()
buf_dmap = reset_buf_dmap()
isPlaying = False
count = 0
wait_frame = 0
message = None
just_reseted = False

while running:
    frames, dmap = get_next_dmap()

    # Crop depth map to keep only the board inbound
    board_dmap = get_board_depth_map(dmap)
    gauss_board = gaussian_filter(board_dmap, sigma=1)

    if np.average(dmap) > 4400:
        del board
        board = Board()
        just_reseted = True
    else:
        if detect_hand(gaussian_filter(board_dmap, sigma=7)):
            isPlaying = True
            count = 0
            wait_frame = 0
            buf_dmap = reset_buf_dmap()
            if not board.finished:
                message = None
        # We wait some frames when the hand is not detected anymore, just to be sure we have a clean depth_map
        elif isPlaying and wait_frame < NB_WAITING_FRAME:
            wait_frame += 1
        elif isPlaying and count < NB_FRAME:
            buf_dmap += gauss_board
            count += 1
        elif isPlaying and count == NB_FRAME and not board.finished:
            # Check which case has been played
            x, y, diff = get_most_diff_case(snapshot_dmap, buf_dmap)
            # If diff is big enough play on detected case
            if diff > MIN_DIFF_ACCEPTED:
                if not board.move(x, y):
                    message = "You can't\nplay there!"
                else:
                    message = None
                    winning_cases = board.won()
                    if len(winning_cases) > 0:
                        message = "END!\n" + board.opponent + " has won."
                    elif board.tied():
                        message = "End by\ndraw!"
                snapshot_dmap = buf_dmap
            else:
                if just_reseted:
                    just_reseted = False
                    message = "Game reset!"
                else:
                    message = "Case not\ndetected!\nTry again!"
            isPlaying = False

    if background:
        rgb_image = build_depth_rgb_image()
        canvas.create_image(0, 0, anchor=tk.NW, image=rgb_image)
    else:
        canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill=BACKGROUND_COLOR)

    draw_grid(message)
    canvas.place(x=canvas_dx, y=canvas_dy)
    root.update()
    listener.release(frames)
    del board_dmap
    del dmap


device.stop()
device.close()

sys.exit(0)
