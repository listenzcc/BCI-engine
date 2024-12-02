"""
File: pandas-speed.py
Author: Chuncheng Zhang
Date: 2024-11-22
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Test the speed limit of the large pandas DataFrame.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-11-22 ------------------------
# Requirements and constants
import time
import contextlib
import numpy as np
import pandas as pd

from loguru import logger
from tqdm.auto import tqdm
from rich import print
from IPython.display import display

from enum import Enum
from pathlib import Path
from threading import Thread, RLock


# %% ---- 2024-11-22 ------------------------
# Function and class
class DataPackageStatus(Enum):
    idle = 0
    collecting = 1
    error = 2


class DataPackage(object):
    channels: int = 256
    package_size: int = 40
    sampling_unit: int = 1  # ms
    channels_name = [str(e) for e in range(channels)]

    # --------------------
    # Variables
    # Data buffer
    data = []
    # How often to report
    check_often_in_seconds = 10
    next_checkpoint_gap = int(check_often_in_seconds * 1000 / sampling_unit)
    next_checkpoint_idx = next_checkpoint_gap

    _rlock = RLock()
    _collect_forever_loop_lock = RLock()
    _status = DataPackageStatus.idle

    def __init__(self):
        pass

    def reset(self):
        self.data = []
        self.next_checkpoint_idx = self.next_checkpoint_gap
        logger.debug('Reset the data package')

    def save(self, path: Path):
        logger.debug(f'Saved the data package into {path}')
        return path

    @contextlib.contextmanager
    def lock(self):
        try:
            self._rlock.acquire()
            yield
        finally:
            self._rlock.release()

    def start_collect(self):
        '''Start the collecting thread.'''
        name = 'collect forever'
        Thread(
            target=self.collect_forever_loop, name=name, daemon=True).start()
        logger.debug(f'Started {name} thread')
        return

    def stop_collect(self):
        if self._status is not DataPackageStatus.collecting:
            logger.warning(f'Can not stop, since the status is {self._status}')
            return

        # The lock makes sure the loop is truly stopped
        try:
            self._status = DataPackageStatus.idle
            logger.debug(f'Changed status to {self._status}')
            self._collect_forever_loop_lock.acquire()
            logger.debug("I believe the collect_forever_loop is stopped.")
        finally:
            self._collect_forever_loop_lock.release()
        return

    def collect_forever_loop(self):
        # Can only start the collect_forever_loop at the idle status.
        if not self._status is DataPackageStatus.idle:
            logger.error(
                f'Can not start collect_forever loop, since the status is {self._status}')
            return

        # Acquire the lock for safety.
        try:
            # Start the loop
            self._collect_forever_loop_lock.acquire()
            self._status = DataPackageStatus.collecting
            self.reset()
            tic = time.time()
            while self._status is DataPackageStatus.collecting:
                self.collect()
            logger.debug(
                f'Stopped collect_forever loop, status is {self._status}')

            # The loop is stopped
            toc = time.time()
            self.tic = tic
            self.toc = toc
            logger.debug(
                f'The tic/toc is {tic}/{toc}, costs {toc-tic} seconds')
        finally:
            self._collect_forever_loop_lock.release()

        return

    def data_to_DataFrame(self):
        '''Convert collected data to a DataFrame.'''
        logger.debug(
            f'Converting {len(self.data)} records into DataFrame, it costs seconds.')
        data = [e[1] for e in self.data]
        ms = [e[0] for e in self.data]
        df = pd.DataFrame(data, columns=self.channels_name)
        df['_ms'] = ms
        self.df = df
        logger.debug(f'Converted {len(df)} records.')
        return df

    def collect(self):
        '''Collect one package'''
        pkg, received_ms = self.pseudo_package()
        with self.lock():
            for d, t in zip(pkg, self.package_range(received_ms)):
                self.data.append((t, d))
            n = len(self.data)
            t0 = self.data[0][0]
            t1 = self.data[-1][0]
        if n > self.next_checkpoint_idx:
            self.next_checkpoint_idx += self.next_checkpoint_gap
            logger.debug(f'Collected {n} records in {t1-t0} seconds')

    def package_range(self, ms: float):
        '''
        Mark every time point of the package
        Compute the time range for each package
        Consider ms is receiving time of the package.
        (ms-package_size*sampling_unit) |<--- package size --->| (ms)
        '''
        return range(ms - self.package_size * self.sampling_unit, ms+1, self.sampling_unit)

    def pseudo_package(self):
        '''Generate pseudo package'''
        # Sleep one package length in seconds
        time.sleep(self.package_size*self.sampling_unit/1000)
        # Convert timestamp into milliseconds
        ms = self.timestamp_to_milliseconds(time.time())
        pkg = np.random.randn(self.package_size, self.channels)
        return pkg, ms

    def timestamp_to_milliseconds(self, timestamp: float) -> int:
        '''Convert timestamp into milliseconds.'''
        return int(timestamp*1000)


data_package = DataPackage()
data_package.start_collect()
input('Press enter to stop collecting.')
data_package.stop_collect()
df = data_package.data_to_DataFrame()
display(df)

# %% ---- 2024-11-22 ------------------------
# Play ground


# %% ---- 2024-11-22 ------------------------
# Pending


# %% ---- 2024-11-22 ------------------------
# Pending
