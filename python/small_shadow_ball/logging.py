"""
File: logging.py
Author: Chuncheng Zhang
Date: 2024-08-08
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Amazing things

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-08-08 ------------------------
# Requirements and constants
import os

from pathlib import Path
from loguru import logger
from .conf import conf


# %% ---- 2024-08-08 ------------------------
# Function and class
projectName = conf.get('projectName', 'NoNamedProject')

logger.add(Path(
    os.environ.get('HOME', '.'), f'log/{projectName}.log'),
    rotation='5 MB')


# %% ---- 2024-08-08 ------------------------
# Play ground


# %% ---- 2024-08-08 ------------------------
# Pending


# %% ---- 2024-08-08 ------------------------
# Pending
