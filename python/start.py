"""
File: start.py
Author: Chuncheng Zhang
Date: 2024-08-07
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


# %% ---- 2024-08-07 ------------------------
# Requirements and constants
import sys
from pathlib import Path

import uvicorn


# %% ---- 2024-08-07 ------------------------
# Function and class
# ! Append the folder into the python system path in the first place
sys.path.append(Path(__file__).parent)


# %% ---- 2024-08-07 ------------------------
# Play ground
if __name__ == "__main__":
    # Use the string import to enable reload option.
    uvicorn.run("fastapi_engine.main:wa.app", reload=True, host="172.20.10.7")


# %% ---- 2024-08-07 ------------------------
# Pending


# %% ---- 2024-08-07 ------------------------
# Pending
