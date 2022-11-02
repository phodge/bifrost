import base64
import os
from typing import Any, Callable, Dict, Optional, Tuple, Union

import requests
from generated_client import (ApiBroken, ApiFailure, ApiOutage,
                              ApiUnauthorized, ClientBase)


class RequestsPythonClient(ClientBase):
    _auth: Optional[Tuple[str, str]] = None

    def __init__(self) -> None:
        self._session = requests.Session()

    def setAuth(self, username: str, password: str) -> None:
        self._auth = (username, password)

    def _dispatch(
        self,
        method: str,
        params: Dict[str, Any],
        converter: Callable[[Any], Any],
    ) -> Union[ApiFailure, Any]:
        port = int(os.environ['DEMO_SERVICE_PORT'])
        host = '127.0.0.1'
        url = f'http://{host}:{port}/api.v1/call/{method}'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        if self._auth is not None:
            authstr: str = base64.b64encode(':'.join(self._auth).encode('utf-8')).decode('utf-8')
            headers['Authorization'] = 'Basic ' + authstr
        result = self._session.post(url, json=params, headers=headers)
        if result.status_code == 401:
            return ApiUnauthorized(
                f'HTTP 401 Unauthorized: {result.text}'
            )
        if result.status_code != 200:
            # TODO: return ApiBroken instead when appropriate
            # TODO: have more descriptive errors for various types of errors
            # TODO: test this code path when we rework errors
            return ApiOutage(
                f'Unexpected HTTP {result.status_code} response from rpc server: {result.text}'
            )

        # read JSON blob or bomb out
        try:
            data = result.json()
        except Exception as e:
            return ApiBroken(f'Response was not valid JOSN: {e.args[0]}')

        try:
            ret = converter(data)
        except TypeError as e:
            return ApiBroken(f'Response data from {method} was invalid: {e.args[0]}')

        return ret
