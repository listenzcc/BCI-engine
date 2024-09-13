"""
File: engine.py
Author: Chuncheng Zhang
Date: 2024-08-07
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Display engine

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-08-07 ------------------------
# Requirements and constants
import sys

from PyQt6.QtCore import Qt, QTimer

from .util import logger, SyncWebsocketTalk
from .util.timer import RunningTimer
from .util.camera import CameraReady
from .util.screen_painter import SSVEPScreenPainter

# Set SSVEPScreenPainter
ssp = SSVEPScreenPainter()

# Set running timer
tr = RunningTimer('Frontend')

# Set CameraReady
cr = CameraReady(width=ssp.width//4, height=ssp.height//6)


# %% ---- 2024-08-07 ------------------------
# Function and class
def _about_to_quit():
    '''
    Safely quit the demo
    '''
    # Stop the screen painter
    ssp.stop()
    logger.debug('Stopped DisplayEngine')

    # Stop the camera
    cr.stop()
    logger.debug('Stopped CameraReady')
    return


def _on_key_pressed(event):
    '''
    Handle the key pressed event.

    Args:
        - event: The pressed event.
    '''

    try:
        key = event.key()
        enum = Qt.Key(key)
        logger.debug(f'Key pressed: {key}, {enum.name}')

        # If esc is pressed, quit the app
        if enum.name == 'Key_Escape':
            ssp.app.quit()

    except Exception as err:
        logger.error(f'Key pressed but I got an error: {err}')


def is_port_in_use(host: str, port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def start_display():
    '''
    Start the SSVEP display
    '''
    # ! Can not start the display if the host:port is in use
    host = SyncWebsocketTalk.host
    port = SyncWebsocketTalk.port
    if is_port_in_use(host, port):
        logger.error(f'Can not start since the {host}:{port} is in use.')
        return

    # Show the window
    ssp.window.show()

    # Reset the timer
    tr.reset()

    # Start the camera looping
    cr.start_capture_threads()

    # Set the painting method
    def _on_timeout():
        tr.step()
        # img = ssp.img.copy()
        img = ssp.safe_get_img()
        img.paste(cr.patch, box=(ssp.width-cr.patch.width, 0))
        ssp.repaint(img)

    timer = QTimer()
    timer.timeout.connect(_on_timeout)
    timer.start()

    # Start the display main loop
    ssp.start()

    ssp._start_ws_serve()

    sys.exit(ssp.app.exec())


# %% ---- 2024-08-07 ------------------------
# Play ground
# Bind the _about_to_quit and _on_key_pressed methods
ssp.app.aboutToQuit.connect(_about_to_quit)
ssp.window.keyPressEvent = _on_key_pressed

# start_display()

# %% ---- 2024-08-07 ------------------------
# Pending


# %% ---- 2024-08-07 ------------------------
# Pending
