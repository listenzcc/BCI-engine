"""
File: main.py
Author: Chuncheng Zhang
Date: 2024-08-07
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Run the fastAPI application

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-08-07 ------------------------
# Requirements and constants
import time
import json
import websockets.sync.client
from multiprocessing import Process

from typing import Annotated

from fastapi import FastAPI, Request, Response, HTTPException, responses, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pathlib import Path

# from loguru import logger
from display_engine.engine import start_display
from . import logger
from . import SyncWebsocketTalk


# %% ---- 2024-08-07 ------------------------
# Function and class
class WebApp(object):
    project_root = Path(__file__).parent
    script_folder = project_root.joinpath('script')
    title = 'BCI Engine with Fast API Support'
    app = FastAPI(title=title)
    jinja2_template: Jinja2Templates = None

    def __init__(self):
        self.mount_path()
        self.mount_jinja2_template()
        logger.info('Initialized')

    def mount_path(self):
        ''' Mount the static folder. '''
        mounts = [
            dict(
                path='/static', name='static',
                directory=self.project_root.joinpath('web/static'))
        ]

        for dct in mounts:
            self.app.mount(
                path=dct['path'], name=dct['name'],
                app=StaticFiles(directory=dct['directory']))
            logger.debug(f'Mounted path {dct}')

    def mount_jinja2_template(self):
        ''' Mount jinja2 template path. '''
        directory = self.project_root.joinpath('web/template')
        self.jinja2_template = Jinja2Templates(directory=directory)
        logger.debug(f'Using jinja2 template path {directory}')
        return

    def something_is_wrong(self, exc):
        '''
        Fetch the details when something is wrong

        Args:
            - exc: The exception.

        Returns:
            - detail (str): The details of the exception.
        '''
        import traceback
        detail = traceback.format_exc()
        print(detail)
        logger.error(exc)
        return detail


# ----------------------------------------
# ---- Must have app in the first place ----
wa = WebApp()
app = wa.app

# %% ---- 2024-08-07 ------------------------
# Routines

swt = SyncWebsocketTalk()


# ----------------------------------------
# ---- Basics ----

@app.get('/')
async def index(request: Request):
    '''Homepage'''
    return wa.jinja2_template.TemplateResponse('page/home.html', {'request': request})


@app.post('/search')
async def search(searchQuery: Annotated[str, Form()]):
    '''Search results'''
    print(searchQuery)
    return searchQuery


@app.get('/test')
async def test(request: Request):
    '''Test websocket connection, using echo method'''
    dct = dict(cmd='echo', body='test message')
    received = swt.send_and_recv(dct)
    logger.debug(f'Received {received}')
    return received


# ----------------------------------------
# ---- SSVEP timing ----

@app.get('/checkoutPassedSeconds.json')
async def checkout_passed_seconds(request: Request):
    '''Query how long the SSVEP displayed'''
    dct = dict(cmd='query passed seconds')
    try:
        received = swt.send_and_recv(dct)
    except ConnectionRefusedError as err:
        logger.error(f'Failed checkout, {err}')
        raise HTTPException(
            status_code=404, detail='Failed checkoutPassedSeconds.json')
    logger.debug(f'Received {received}')
    return received


# ----------------------------------------
# ---- SSVEP append chars ----
@app.get('/appendPreDefinedSequence.json')
async def append_predefined_sequence(request: Request, text: str):
    '''Append the text into the SSVEP predefined_sequence

    Args:
        - request: The request.
        - text [str]: The text to be appended.

    Returns:
        - received [dict]: The dictionary containing the raw input, status and updated sequence.
    '''
    dct = dict(cmd='append predefined sequence', text=text)
    try:
        received = swt.send_and_recv(dct)
    except ConnectionRefusedError as err:
        logger.error(f'Failed checkout, {err}')
        raise HTTPException(
            status_code=404, detail='Failed appendPredefinedSequence')
    logger.debug(f'Received {received}')
    return received


# ----------------------------------------
# ---- SSVEP control ----


@app.get('/startSSVEPDisplay')
async def start_ssvep_display(request: Request):
    '''Require to start the SSVEP display in the separate Process'''
    Process(target=start_display, daemon=True).start()
    return ''


@app.get('/ssvepLayoutColumns')
async def change_ssvep_layout_columns(request: Request, columns: int):
    '''Change the SSVEP layout columns'''
    dct = dict(cmd='change columns', columns=columns)
    try:
        received = swt.send_and_recv(dct)
    except ConnectionRefusedError as err:
        logger.error(f'Failed checkout, {err}')
        raise HTTPException(
            status_code=404, detail='Failed checkoutPassedSeconds.json')
    logger.debug(f'Received {received}')
    return received


# Process(target=start_display, daemon=True).start()

# %% ---- 2024-08-07 ------------------------
# Play ground

# %% ---- 2024-08-07 ------------------------
# Pending

# %% ---- 2024-08-07 ------------------------
# Pending
