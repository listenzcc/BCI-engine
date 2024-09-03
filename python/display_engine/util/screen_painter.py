"""
File: screen_painter.py
Author: Chuncheng Zhang
Date: 2024-08-07
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Screen painter with websocket connection server

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
import json
import time
import opensimplex
import numpy as np

from threading import Thread, RLock
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageQt import ImageQt

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

from . import logger, SyncWebsocketTalk
from .timer import RunningTimer

small_font = ImageFont.truetype("arial.ttf", 24)
large_font = ImageFont.truetype("arial.ttf", 64)

# %% ---- 2024-08-07 ------------------------
# Function and class
_app = QApplication(sys.argv)

swt = SyncWebsocketTalk()


class SSVEPLayout(object):
    w = 0  # left bound
    e = 100  # right bound
    n = 0  # top bound
    s = 100  # bottom bound
    columns = 6  # number of columns
    paddingRatio = 0.2
    char_sequence = [e for e in 'abcdefghijklmnopqrstuvwxyz1234567890']

    def reset_box(self, w, n, e, s):
        self.w = w
        self.e = e
        self.n = n
        self.s = s

    def reset_columns(self, columns):
        self.columns = columns

    def shuffle_char_sequence(self):
        np.random.shuffle(self.char_sequence)

    def get_layout(self):
        '''
            Patch layout:
                        n
                1, 2, 3, ............ 
                c+1, c+2, c+3, ......
                2c+1, 2c+2, 2c+3, ...
            w   .....................    e
                .....................
                .....................
                rc+1, rc+2, rc+3, ...
                        s

            Patch size:
            +------- d -------+
            |                 |
            |  (x, y)-----+   |
            |    |        |   |
            |    |        |   |
            |    +--size--+   |
            |                 |
            +-----------------+

        '''
        ws = np.linspace(self.w, self.e, self.columns+1)[:-1]
        d = int(ws[1] - ws[0])
        rows = int((self.s - self.n) / d)
        size = int((ws[1] - ws[0]) * (1-self.paddingRatio))

        layout = []
        patch_id = 0
        for i in range(rows):
            for j in range(self.columns):
                layout.append(dict(
                    patch_id=patch_id,
                    size=size,
                    x=int(self.w + d * j + (d-size)/2),
                    y=int(self.n + d * i + (d-size)/2),
                    char=self.char_sequence[patch_id % len(self.char_sequence)]
                ))
                patch_id += 1
        return layout


ssvep_layout = SSVEPLayout()


class SSVEPScreenPainter(object):
    '''
    SSVEP ScreenPainter
    '''

    # Generate app first
    app = _app

    # Components
    window = QMainWindow()
    pixmap_container = QLabel(window)
    rt = RunningTimer('BackendTimer')

    # Parameters in waiting
    width: int = None
    height: int = None
    img: Image = None
    img_drawer: ImageDraw = None
    pixmap: QPixmap = None

    on_going_thread: Thread = None

    # Options
    flag_has_focus: bool = True
    rlock = RLock()

    def __init__(self):
        '''
        Initialize by default
        '''
        self.prepare_window()
        self.empty_img()
        self._handle_focus_change()
        logger.info('Initialized engine')

    def _handle_focus_change(self):
        '''
        Handle the focus change event.
        '''
        def focus_changed(e):
            self.flag_has_focus = e is not None
            logger.debug(f'Focus changed to {self.flag_has_focus}')
        self.app.focusWindowChanged.connect(focus_changed)
        logger.debug(f'Handled focus changed with {focus_changed}')
        return

    def show(self):
        '''
        Show the window
        '''
        self.window.show()
        logger.debug('Shown window')
        return

    def prepare_window(self):
        '''
        Prepare the window,
        - Set its size, position and transparency.
        - Set the self.pixmap_container geometry accordingly.
        '''
        # Translucent image by its RGBA A channel
        self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Disable frame and keep the window on the top layer
        # It is necessary to set the FramelessWindowHint for the WA_TranslucentBackground works
        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)

        # Only hide window frame
        # self.window.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Fetch the screen size and set the size for the window
        screen = self.app.primaryScreen()
        self.width = screen.size().width() // 2
        self.height = screen.size().height()

        # Set the window size
        self.window.resize(self.width, self.height)

        # Put the window to the right
        self.window.move(self.width, 0)

        # Set the pixmap_container accordingly,
        # and it is within the window bounds
        self.pixmap_container.setGeometry(0, 0, self.width, self.height)

        logger.debug(
            f'Reset window size to {self.width}, {self.width}, and reset other stuff')
        return

    def empty_img(self):
        '''
        Prepare the img and its relating,
        - Set the img object, its size and drawer.
        - Repaint with it for startup.
        '''
        # Generate fully transparent image and its drawer
        self.img = Image.fromarray(
            np.zeros((self.width, self.height, 4), dtype=np.uint8)).convert('RGBA')
        self.img_drawer = ImageDraw.Draw(self.img)

        # Repaint with default img for startup
        self.repaint()

        logger.debug(f'Prepared img, {self.img}, {self.img_drawer}')
        return

    def repaint(self, img: Image = None):
        '''
        Repaint with the given img.
        If it is None, using self.img as default.

        The pipeline is
        img -> pixmap -> pixmap_container

        Args:
            - img: Image object, default is None.
        '''

        # Use self.img if nothing is provided
        if img is None:
            img = self.img

        # img -> pixmap
        self.remake_pixmap(img)

        # pixmap -> pixmap_container
        self.pixmap_container.setPixmap(self.pixmap)

        return

    def remake_pixmap(self, img: Image = None):
        '''
        Remake the self.pixmap with the input img.

        Args:
            - img: Image object.
        '''
        self.pixmap = QPixmap.fromImage(ImageQt(img))
        return

    def start(self):
        ''' Start the main_loop '''
        if self.on_going_thread:
            logger.error(
                f'Failed to start the main_loop since one is already running, {self.on_going_thread}.')
            return

        self.on_going_thread = Thread(target=self.main_loop, daemon=True)
        self.on_going_thread.start()
        return

    def stop(self):
        ''' Stop the running main loop '''
        if not self.on_going_thread:
            logger.error(
                'Failed to stop the main_loop since it is not running.')
            return

        # Tell the main_loop to stop.
        self.rt.running = False

        # Wait for the main_loop to stop.
        logger.debug('Waiting for main_loop to stop.')
        self.on_going_thread.join()
        logger.debug('Stopped the main_loop.')

        # Reset the self.on_going_thread to None
        self.on_going_thread = None

        return

    def safe_get_img(self):
        with self.rlock:
            return self.img

    def main_loop(self):
        ''' Main loop for SSVEP display. '''
        self.rt.reset()

        # Reset the ssvep layout box
        ssvep_layout.reset_box(0, self.height/6, self.width, self.height)

        # The flipping rate is slower when the speed_factor is lower
        speed_factor = 1

        change_char_step = 5  # seconds
        change_char_next_passed = change_char_step
        ssvep_layout.shuffle_char_sequence()

        logger.debug('Starting')
        while self.rt.running:
            # Update the timer to the next frame
            self.rt.step()

            # Get the current time
            passed = self.rt.get()
            if passed > change_char_next_passed:
                change_char_next_passed += change_char_step
                ssvep_layout.shuffle_char_sequence()
                self.empty_img()

            # Get layout
            layout = ssvep_layout.get_layout()
            # Modify the passed seconds with speed_factor
            z = passed * speed_factor
            with self.rlock:
                for p in layout:
                    x = p['x']
                    y = p['y']
                    size = p['size']
                    patch_id = p['patch_id']
                    char = p['char']
                    f = (opensimplex.noise3(x=x, y=y, z=z)+1) * 0.5
                    c = int(f * 256)
                    self.img_drawer.rectangle(
                        (x, y, x+size, y+size), fill=(c, c, c, c))
                    self.img_drawer.text(
                        (x, y), f'{patch_id}', font=small_font)
                    self.img_drawer.text(
                        (x+size/2, y+size/2), char, font=large_font, anchor='mm')

            # Blink on the right top corner in 50x50 pixels size if not focused
            if not self.flag_has_focus:
                c = tuple(np.random.randint(0, 256, 3))
                self.img_drawer.rectangle(
                    (self.width-50, 0, self.width, 50), fill=c)

            # Paint
            self._on_paint_subsystem()
            # self.repaint()

            # Continue after sleep
            time.sleep(0.001)
            pass
        logger.debug('Stopped')
        return

    def _on_paint_subsystem(self):
        '''Subsystem requires rewrite'''
        return

    def _ws_handler(self, ws):
        '''Handle incoming websocket requests '''
        for message in ws:
            # Load json package
            message = json.loads(message)
            logger.debug(f'Ws server received {message}')

            # Get cmd from the message
            cmd = message.get('cmd')

            # ----------------------------------------
            # ---- Switch by cmd ----

            # Echo back the message
            if cmd == 'echo':
                message.update(status='Success')

            # Query how long the SSVEP displaying passed
            elif cmd == 'query passed seconds':
                message.update(
                    status='Success', passed=self.rt.get())

            # Change the columns
            elif cmd == 'change columns':
                # Reset columns
                ssvep_layout.reset_columns(message['columns'])
                # Empty the img
                self.empty_img()
                message.update(status='Success')

            # Unknown command
            else:
                message.update(
                    status='Fail', error='Unknown command')
                logger.warning(f'Unknown command {message}')

            # Timestamp the message and send the updated message back
            message.update(timestamp=time.time())
            ws.send(json.dumps(message))

        return

    def _start_ws_serve(self):
        ''' Start the websocket server in the thread. '''
        Thread(target=swt.serve_forever, args=(
            self._ws_handler,), daemon=True).start()


# %% ---- 2024-08-07 ------------------------
# Play ground


# %% ---- 2024-08-07 ------------------------
# Pending


# %% ---- 2024-08-07 ------------------------
# Pending