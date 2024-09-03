"""
File: websocket_sync.py
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
import json
import time
import websockets.sync.client
import websockets.sync.server


# %% ---- 2024-08-08 ------------------------
# Function and class

class SyncWebsocketTalk:
    host = 'localhost'
    port = 8891
    uri = f'ws://{host}:{port}'

    def send_and_recv(self, dct: dict) -> dict:
        '''
        Working on the client side.

        Send the dict message to the websocket server and wait for the response

        Args:
            - dct (dict): The message to send.

        Returns:
            - received (dict): The received message.
        '''
        # Timestamp the message
        dct.update({'_send': time.time()})

        with websockets.sync.client.connect(self.uri) as ws:
            # Send
            ws.send(json.dumps(dct))
            # Receive
            received = json.loads(ws.recv())

        received.update({'_received': time.time()})
        return received

    def serve_forever(self, handler):
        '''
        Working on the server side.

        Serve forever
        '''
        with websockets.sync.server.serve(handler, host=self.host, port=self.port) as server:
            print('-' * 800)
            server.serve_forever()

# %% ---- 2024-08-08 ------------------------
# Play ground


# %% ---- 2024-08-08 ------------------------
# Pending


# %% ---- 2024-08-08 ------------------------
# Pending
