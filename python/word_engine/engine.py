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
import random
from loguru import logger


# %% ---- 2024-09-11 ------------------------
# Function and class
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
    pre_designed_sequence: list = list('观自在菩萨')
    prompt: list = []

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

    def mk_layout(self, num_patches=None, fixed_positions=None):
        if num_patches is None:
            num_patches = self.num_patches

        if fixed_positions is None:
            fixed_positions = self.fixed_positions

        indices = [e for e in range(self.num_patches)
                   if e not in fixed_positions]
        random.shuffle(self.other_chars)
        sequence = self.other_chars[:num_patches]
        for k, v in fixed_positions.items():
            sequence[k] = v

        cue_index = random.choice(indices)
        if self.pre_designed_sequence:
            sequence[cue_index] = self.pre_designed_sequence[0]

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
            self.prompt.append(inp)
        return self.prompt


# %% ---- 2024-09-11 ------------------------
# Play ground


# %% ---- 2024-09-11 ------------------------
# Pending


# %% ---- 2024-09-11 ------------------------
# Pending
