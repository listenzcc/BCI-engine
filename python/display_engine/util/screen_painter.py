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
import random
import itertools
import opensimplex
import numpy as np

from enum import Enum
from threading import Thread, RLock
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageQt import ImageQt

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

from word_engine.engine import SSVEPWordBag, SendToWindowsApp, get_app_and_titles

from . import logger, SyncWebsocketTalk
from .timer import RunningTimer

small_font = ImageFont.truetype("arial.ttf", 24)
large_font = ImageFont.truetype("arial.ttf", 64)
small_font = ImageFont.truetype("c:\\windows\\fonts\\msyhl.ttc", 24)
large_font = ImageFont.truetype("c:\\windows\\fonts\\msyhl.ttc", 64)


# %% ---- 2024-08-07 ------------------------
# Function and class
_app = QApplication(sys.argv)

swt = SyncWebsocketTalk()

swb = SSVEPWordBag()

stwa = SendToWindowsApp()


class SSVEPInputStage(Enum):
    awaitInputWithCue = 1
    awaitInputWithoutCue = 2
    awaitEnter = 3
    awaitApp = 4
    default = 5


class SSVEPLayout(object):
    w = 0  # left bound
    e = 100  # right bound
    n = 0  # top bound
    s = 100  # bottom bound
    columns: int = 6  # number of columns
    rows: int = 6
    paddingRatio = 0.2
    char_sequence = [e for e in 'abcdefghijklmnopqrstuvwxyz1234567890']
    cue_index: int = 0

    def reset_box(self, w, n, e, s):
        self.w = w
        self.e = e
        self.n = n
        self.s = s

    def reset_columns(self, columns):
        self.columns = columns

    def _deprecated_shuffle_char_sequence(self):
        np.random.shuffle(self.char_sequence)

        # Get layout
        layout = self.get_layout()

        # Setup swb
        n = len(layout)
        sequence, cue_index = swb.mk_layout(
            num_patches=n,
            fixed_positions={n-3: 'Back', n-2: 'Space', n-1: 'Enter'})

        self.char_sequence = sequence
        self.cue_index = cue_index
        return n

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

        layout = [
            dict(
                patch_id=patch_id,
                size=size,
                x=int(self.w + d * j + (d - size) / 2),
                y=int(self.n + d * i + (d - size) / 2),
                char=self.char_sequence[patch_id % len(self.char_sequence)],
            )
            for patch_id, (i, j) in enumerate(
                itertools.product(range(rows), range(self.columns))
            )
        ]

        self.rows = rows
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
        header_height = self.height/6
        ssvep_layout.reset_box(0, header_height, self.width, self.height)

        # The flipping rate is slower when the speed_factor is lower
        speed_factor = 1

        change_char_step = 4  # seconds
        change_char_next_passed = change_char_step

        # The stage flag for the sending protocol
        class SendingProtocolStage:
            stage = SSVEPInputStage.default

        sps = SendingProtocolStage()

        # ssvep_layout.shuffle_char_sequence()

        def _on_trial_stops():
            '''Called when the trial stops, prepare to the next trial.'''
            # n = ssvep_layout.shuffle_char_sequence()

            # ----------------------------------------
            # ---- Consume input chars ----
            # ! Now it is only applied for input with cue
            if sps.stage is SSVEPInputStage.awaitInputWithCue:
                swb.append_prompt(swb.consume(swb.cue_sequence[0]))

            # ----------------------------------------
            # ---- Determine stage ----

            # The latest stage is awaitEnter, so this trial selects app to send.
            # ! This option rejects other stages.
            if sps.stage is SSVEPInputStage.awaitEnter:
                # Get patches layout
                # ! incase I need another layout for the app selection trial
                layout = ssvep_layout.get_layout()
                n = len(layout)

                # Manually control the patches face
                # Get all the apps in the current desktop,
                # and mark the titles (could be used as cue) as the cue candidates.
                fixed_positions = {k: '' for k in range(n)}
                cue_candidate_list = []
                for i, dct in enumerate(get_app_and_titles()[:n]):
                    title = dct['title']
                    fixed_positions.update({i: title})
                    if any([title.endswith(' - 记事本'), title.endswith(' - Word')]):
                        cue_candidate_list.append(i)

                # fixed_positions.update({0: '无标题 - 记事本', 1: '文档1 - Word'})

                sequence, cue_index = swb.mk_layout(
                    num_patches=n, fixed_positions=fixed_positions)

                # Save the layout
                ssvep_layout.char_sequence = sequence
                if cue_candidate_list:
                    ssvep_layout.cue_index = random.choice(cue_candidate_list)
                else:
                    ssvep_layout.cue_index = None

                # Switch the stage
                sps.stage = SSVEPInputStage.awaitApp

                return

            # Pass through the awaitApp stage
            elif sps.stage is SSVEPInputStage.awaitApp:
                pass

            # No cue available and prompt is NOT empty,
            # it is ready to enter for sending the prompt.
            elif all([len(swb.cue_sequence) == 0, len(swb.prompt_buffer) > 0]):
                sps.stage = SSVEPInputStage.awaitEnter

            # No cue available and prompt is empty,
            # it is freedom input.
            elif all([len(swb.cue_sequence) == 0, len(swb.prompt_buffer) == 0]):
                sps.stage = SSVEPInputStage.awaitInputWithoutCue

            # Cue available, it is cued input.
            elif all([len(swb.cue_sequence) > 0]):
                sps.stage = SSVEPInputStage.awaitInputWithCue

            else:
                logger.error(f'Met incorrect stage: {sys.stage}')

            # ----------------------------------------
            # ---- Operations ----

            # Get patches layout
            layout = ssvep_layout.get_layout()
            n = len(layout)

            # Handle normal input stage
            if sps.stage in [SSVEPInputStage.awaitInputWithCue, SSVEPInputStage.awaitInputWithoutCue]:
                sequence, cue_index = swb.mk_layout(
                    num_patches=n,
                    fixed_positions={n-3: 'Back', n-2: 'Space', n-1: 'Enter'})
                ssvep_layout.char_sequence = sequence
                ssvep_layout.cue_index = cue_index

            # Handle enter input stage
            if sps.stage is SSVEPInputStage.awaitEnter:
                sequence, cue_index = swb.mk_layout(
                    num_patches=n,
                    fixed_positions={n-3: 'Back', n-2: 'Space', n-1: 'Enter'})

                if cue_index != -1:
                    logger.warning(
                        f'The cue_index supports to be -1, but it is actually: {cue_index}')

                ssvep_layout.char_sequence = sequence
                ssvep_layout.cue_index = n-1

            # App selection
            if sps.stage is SSVEPInputStage.awaitApp:
                # Send the prompt to the app
                app_title = ssvep_layout.char_sequence[ssvep_layout.cue_index]
                content = ''.join(swb.prompt_buffer)
                swb.prompt_buffer = []
                try:
                    stwa.send(content, app_title)
                    logger.debug(
                        f'The selected app is {app_title}, and the sending content is {content}')
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    logger.error(f'Failed send {content} to app: {app_title}')

                # Restore the stage
                sps.stage = SSVEPInputStage.default

                # Execute itself AGAIN to update the layout
                _on_trial_stops()

            return

        # Execute the _on_trial_stops for a good startup
        _on_trial_stops()
        # Get layout
        layout = ssvep_layout.get_layout()
        # Empty the img to clear the latest patches content.
        self.empty_img()

        logger.debug('Starting')
        while self.rt.running:
            # Update the timer to the next frame
            self.rt.step()

            # Get the current time
            passed = self.rt.get()

            # If the trial finished, shuffle the sequence for the next trial
            # ! It is called when the trial stops.
            if passed > change_char_next_passed:
                # Step the time passed threshold to the next trial.
                change_char_next_passed += change_char_step
                # Execute the _on_trial_stops handler.
                _on_trial_stops()
                # Get layout
                layout = ssvep_layout.get_layout()
                # Empty the img to clear the latest patches content.
                self.empty_img()

            # Compute trial ratio
            tr = (change_char_next_passed - passed) / change_char_step

            # Modify the passed seconds with speed_factor
            z = passed * speed_factor
            with self.rlock:
                # Draw the prompt
                prompt = ''.join(swb.prompt_buffer)
                self.img_drawer.text(
                    (0, header_height/2), prompt, font=large_font, anchor='lt')

                # Draw the progressing bar
                self.img_drawer.rectangle(
                    (0, header_height-2, self.width, header_height),
                    fill=(150, 150, 150, 0)
                )
                self.img_drawer.rectangle(
                    (0, header_height-2, tr*self.width, header_height),
                    fill=(150, 150, 150, 150)
                )

                for i, p in enumerate(layout):
                    # Draw the patch
                    x = p['x']
                    y = p['y']
                    size = p['size']
                    patch_id = p['patch_id']
                    char = p['char']
                    f = (opensimplex.noise3(x=x, y=y, z=z)+1) * 0.5
                    c = int(f * 256)

                    # Draw the box
                    self.img_drawer.rectangle(
                        (x, y, x+size, y+size), fill=(c, c, c, c))

                    # Draw the cue hinter
                    if i == ssvep_layout.cue_index:
                        self.img_drawer.rectangle(
                            (x+size*0.8, y, x+size, y+size*0.2), fill=(150, 0, 0, 255))

                    # Draw the index number
                    self.img_drawer.text(
                        (x, y), f'{patch_id}', font=small_font)

                    # Draw the face char
                    _font = large_font if len(char) == 1 else small_font
                    _char = char
                    if len(char) > 7:
                        _char = '...'.join((char[:3], char[-3:]))
                    self.img_drawer.text(
                        (x+size/2, y+size/2), _char, font=_font, anchor='mm')

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

            # Append the text into the predefined sequence
            elif cmd == 'append cue sequence':
                text = message.get('text')
                seq = list(text)
                swb.cue_sequence.extend(seq)
                message.update(status='Success', updated=''.join(
                    swb.cue_sequence))

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
