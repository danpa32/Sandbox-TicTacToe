
# coding: utf-8

import numpy as np
import cv2
import sys
import pylab as pl
import matplotlib.cm as cm
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel

try:
    from pylibfreenect2 import OpenGLPacketPipeline
    pipeline = OpenGLPacketPipeline()
except:
    from pylibfreenect2 import CpuPacketPipeline
    pipeline = CpuPacketPipeline()

# Create and set logger
logger = createConsoleLogger(LoggerLevel.Debug)
setGlobalLogger(logger)

fn = Freenect2()
num_devices = fn.enumerateDevices()
if num_devices == 0:
    print("No device connected!")
    sys.exit(1)

serial = fn.getDeviceSerialNumber(0)
device = fn.openDevice(serial, pipeline=pipeline)

listener = SyncMultiFrameListener(FrameType.Ir | FrameType.Depth)

# Register listeners
#device.setColorFrameListener(listener)
device.setIrAndDepthFrameListener(listener)

device.start()

fig = None
img = None

dmap_prev = None

while True:
    frames = listener.waitForNewFrame()

    depth = frames["depth"]

    # depth is measured in millimeters and stored as a 512x424 float32 array
    dmap = depth.asarray()
    dmap = np.clip(4500 - dmap, 0, 4500)
    #dmap = dmap[::-1,::-1]
    dmap = dmap[:,::-1]

    if dmap_prev is not None:
        alpha = 0.9
        dmap = (1 - alpha) * dmap + alpha * dmap_prev
        dmap_prev = dmap
    if False:
        print '--'
        print dmap.dtype
        print dmap.shape
        print dmap.min(), dmap.max()

    if False:
        vis_dmap = dmap / 4500.
        vmin, vmax = 1000, 2000
        vis_dmap = (dmap - vmin) / (vmax - vmin)
        vis_dmap = np.clip(vis_dmap, 0, 1)
        print vis_dmap.min(), vis_dmap.max()
        vis_dmap = cm.jet(vis_dmap)
        cv2.imshow("depth", vis_dmap)
    else:
        if img is None:
            fig = pl.figure(figsize=(16,16))
            #img = pl.imshow(dmap, vmin=1200, vmax=1500)
            img = pl.imshow(dmap, vmin=3340, vmax=3470)
            #img = pl.contour(dmap)
            #img = pl.imshow(dmap, vmin=0, vmax=4500)
            #pl.xlim((150, 350))
            #pl.ylim((110, 240))
            pl.colorbar()
            fig.show()
        else:
            img.set_data(dmap)
            #pl.clf()
            #pl.imshow(dmap, vmin=3250, vmax=3400)
            #pl.contour(dmap, np.linspace(3250, 3400, 10))
            #pl.axes().set_aspect('equal')
            fig.canvas.draw()

    #cv2.imshow("depth", dmap / 4500.)

    listener.release(frames)

    key = cv2.waitKey(delay=1)
    if key == ord('q'):
        break

device.stop()
device.close()

sys.exit(0)
