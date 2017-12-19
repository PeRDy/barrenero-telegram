import logging
from typing import Any, Dict

import requests

from bot.exceptions import BarreneroRequestException

logger = logging.getLogger(__name__)


class Barrenero:
    @staticmethod
    def _get(base_url: str, path: str, token: str) -> Dict[str, Any]:
        try:
            url = base_url + path
            headers = {'Authorization': f'Token {token}'}

            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
        except requests.HTTPError as e:
            raise BarreneroRequestException('Cannot request Barrenero API') from e

        return response.json()

    @staticmethod
    def _post(base_url: str, path: str, token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = base_url + path
            headers = {'Authorization': f'Token {token}'}

            response = requests.post(url=url, headers=headers, data=data)
            response.raise_for_status()
        except requests.HTTPError as e:
            raise BarreneroRequestException('Cannot request Barrenero API') from e

        return response.json()

    @staticmethod
    def get_token_or_register(url: str, username: str, password: str, account: str=None, api_password: str=None) \
            -> Dict[str, Any]:
        try:
            # Try to register user
            register_url = f'{url}/api/v1/auth/register/'
            data = {'username': username, 'password': password, 'account': account, 'api_password': api_password}
            response_register = requests.post(url=register_url, data=data)

            # If user is registered, try to get token using username and password
            if response_register.status_code == 409:
                login_url = f'{url}/api/v1/auth/user/'
                data = {'username': username, 'password': password}

                response_user = requests.post(url=login_url, data=data)
                response_user.raise_for_status()
                payload = response_user.json()
            else:
                response_register.raise_for_status()
                payload = response_register.json()
        except requests.HTTPError:
            raise
        else:
            config = {
                'token': payload['token'],
                'superuser': payload['is_api_superuser'],
            }

        return config

    @staticmethod
    def miner(url: str, token: str) -> Dict[str, Any]:
        return Barrenero._get(base_url=url, path='/api/v1/status/', token=token)

    @staticmethod
    def storj(url: str, token: str) -> Dict[str, Any]:
        return Barrenero._get(base_url=url, path='/api/v1/storj/', token=token)

    @staticmethod
    def wallet(url: str, token: str) -> Dict[str, Any]:
        return Barrenero._get(base_url=url, path='/api/v1/wallet/', token=token)

    @staticmethod
    def restart(url: str, token: str, service: str) -> Dict[str, Any]:
        return Barrenero._post(base_url=url, path='/api/v1/restart/', token=token, data={'name': service})
