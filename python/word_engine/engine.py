"""
File: engine.py
Author: Chuncheng Zhang
Date: 2024-09-11
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    The word engine for word forwarding.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-09-11 ------------------------
# Requirements and constants
import time
import pyvda
import random
import win32gui
import keyboard

from loguru import logger


# %% ---- 2024-09-11 ------------------------
# Function and class
def get_all_desktops():
    '''
    https://github.com/Ciantic/VirtualDesktopAccessor
    '''
    desktops = pyvda.get_virtual_desktops()
    return desktops


def get_title(app: pyvda.AppView) -> str:
    '''
    Get the title of the application.

    Args:
        - app: The application to switch to.

    Returns:
        - (str): The title of the application.
    '''
    return win32gui.GetWindowText(app.hwnd)


def switch_to_app(app: pyvda.AppView, dry_run: bool = False):
    '''
    Switch to the application.

    Args:
        - app: The application to switch to.
        - dry_run (bool, default by False): Whether to prevent switching to the application.
    '''
    if dry_run:
        title = get_title(app)
        name = app.desktop.name
        print(
            f'Dry run switch to desktop: "{name}", title: "{title}"')
        return

    # Switch to the desktop
    app.desktop.go()
    # Focus to the app
    app.set_focus()
    return


class SendToWindowsApp(object):
    '''
    Send text to windows application.
    '''
    title = '微信'

    def send(self, string: str, app_title: str = None):
        '''
        Send the string to the window of title.

        Args:
            - app_title (str): The title of the application to send to.
            - string (str) : The string to be sent.
        '''
        if app_title is None:
            app_title = self.title

        # Get all the applications
        applications = pyvda.get_apps_by_z_order(current_desktop=False)

        # Remember the current application
        current_application = pyvda.AppView.current()

        # Filter the applications according to its title
        applications = [
            app for app in applications if get_title(app) == app_title]

        # Set the interval for safety sending
        interval = 0.2  # Seconds

        for app in applications[:1]:
            switch_to_app(app, dry_run=False)
            time.sleep(interval)
            logger.debug(f'Switched to application: {app}')
            keyboard.write(string, delay=0)
            keyboard.press_and_release('Enter')
            time.sleep(interval)
            logger.debug(f'Sent content: {string}')

        switch_to_app(current_application, dry_run=False)
        logger.debug(f'Restoring to the application: {current_application}')
        return


class SSVEPWordBag(object):
    '''
    The word bag for SSVEP keyboard.

    - num_patches: How many patches in total.
    - fixed_positions: The dict of the fixed patches,
        the key is the index of the patch;
        the value is the value of the patch.
    '''
    num_patches: int = 12
    fixed_positions: dict = {10: 'Back', 11: 'Space', 12: 'Enter'}
    other_chars: list = list('abcdefghijklmnopqrstuvwxyz1234567890')
    # pre_designed_sequence: list = list('观自在菩萨')
    pre_designed_sequence: list = list('观自')
    prompt_buffer: list = []

    def __init__(self):
        logger.debug('Initialized')

    def load_words(self, other_chars: list):
        self.other_chars = other_chars
        logger.debug(f'Loaded other_chars: {other_chars}')
        return

    def load_cue_sequence(self, cue_sequence: list):
        self.pre_designed_sequence = cue_sequence
        logger.debug(f'Loaded cue_sequence: {cue_sequence}')
        return

    def mk_layout(self, num_patches: int = None, fixed_positions: dict = None):
        '''
        Make the layout for the SSVEP display.

        Args:
            num_patches (int): The number of the patches.
            fixed_positions (dict): The fixed positions.

        Returns:
            sequence (list): The char sequence.
            cue_index (int): The index of the cue patch, return -1 if there isn't cue available.
        '''
        # Fetch the default options if not available
        if num_patches is None:
            num_patches = self.num_patches

        if fixed_positions is None:
            fixed_positions = self.fixed_positions

        # Fill the patches with the self.other_chars
        random.shuffle(self.other_chars)
        sequence = self.other_chars[:num_patches]
        for k, v in fixed_positions.items():
            sequence[k] = v

        if self.pre_designed_sequence:
            # Get all the indices for the patches not in the fixed_positions
            indices = [
                e for e in range(self.num_patches) if e not in fixed_positions]
            # Make sure the pre_designed_sequence's top element is in the layout, randomly.
            cue_index = random.choice(indices)
            sequence[cue_index] = self.pre_designed_sequence[0]
        else:
            cue_index = -1

        return sequence, cue_index

    def consume(self, inp: str) -> str:
        '''
        Consume the input string from the self.cue_sequence.

        Args:
            - inp (str): The input string to consume.

        Returns:
            - None if consume failed.
            - The same as inp if consume succeeded.
        '''
        # Return None when cue_sequence is empty
        if not self.pre_designed_sequence:
            return

        # Check whether the first element is inp.
        # If so, pop and return the 1st element.
        # If not so, return None and do not pop.
        return self.pre_designed_sequence.pop(0) if inp == self.pre_designed_sequence[0] else None

    def append_prompt(self, inp: str):
        '''
        Append the input string to the prompt.

        Args:
            - inp (str): The input string to append to the prompt.

        Returns:
            - self.prompt: The appended prompt.
        '''
        # Prevent the inp is empty or None
        if inp:
            self.prompt_buffer.append(inp)
        return self.prompt_buffer


# %% ---- 2024-09-11 ------------------------
# Play ground


# %% ---- 2024-09-11 ------------------------
# Pending


# %% ---- 2024-09-11 ------------------------
# Pending
