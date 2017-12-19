import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class Barrenero:
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
            logger.exception('Cannot retrieve Barrenero API token')
            raise
        else:
            config = {
                'token': payload['token'],
                'superuser': payload['is_api_superuser'],
            }

        return config
