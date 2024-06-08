"""layan-t.net services connector"""

import requests
import os
from typing import Optional, Dict, Any, List
import jwt
from datetime import datetime

from esimslib.connectors.aws_connector import SSMConnector as ssm

from constants import LayanTConst as layan_constants
from concurrent.futures import ThreadPoolExecutor, as_completed


class LayanConnector:
    """Layan-T Connector to run Layan-T Tasks"""

    def __init__(self, username: str = None, password: str = None):
        self._base_url: str = layan_constants.API_URL
        if username:
            self._username = username
        else:
            self._username: str = ssm().get_parameter(os.getenv(layan_constants.LAYANT_USERNAME))
       
        if password:
            self._password = password
        else:
            self._password: str = ssm().get_parameter(os.getenv(layan_constants.LAYANT_PASSWORD))
        
        self._token: str = self._get_token()
        self._headers: Dict[str, str] = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json',
            'LANG': 'ar'
        }


    def _get_token(self) -> str:
        token: Optional[str] = self._read_token_from_env()
        
        if not token or self._is_token_invalid(token):
            token = self._refresh_token()
        
        return token

    def _read_token_from_ssm(self) -> Optional[str]:
        try:
            return ssm().get_parameter(os.getenv(layan_constants.LAYANT_TOKEN))
        except Exception as e:
            print(f'Error reading the token from file: {e}')
            return None
    def _save_token_to_env(self, token: str) -> None:
        try:
            ssm.update_parameter(os.getenv(layan_constants.LAYANT_TOKEN), token, True)
        except Exception as e:
            print(f'Error saving the token to file: {e}')

    # TODO: Handle the case where the username/password combination is incorrect
    def _refresh_token(self) -> str:
        try:

            auth_data = {
                'username': self._username,
                'password': self._password
            }

            response = requests.post(
                url=f'{self._base_url}Auth/Login',
                json=auth_data
            )
            response.raise_for_status()
            token = response.json().get('data').get('jwt')
            self._save_token_to_env(token)
            return token
        except Exception as e:
            print(f'Error refreshing the token: {e}')
            return ""

    def _is_token_invalid(self, token: str) -> bool:
        try:
            payload: Dict[str, Any] = jwt.decode(token, options={"verify_signature": False})
            exp: Optional[int] = payload.get('exp')
            if exp and datetime.fromtimestamp(exp) > datetime.now():
                return False
            return True
        except Exception as e:
            print(f'Error decoding the token: {e}')
            return True

    def _ensure_token_valid(self) -> None:
        if self._is_token_invalid(self._token):
            self._token = self._refresh_token()
            self._headers['Authorization'] = f'Bearer {self._token}'

    def _get_request(self, endpoint: str) -> requests.Response:
        self._ensure_token_valid()
        url: str = f'{self._base_url}{endpoint}'
        response = requests.get(url, headers=self._headers)
        response.raise_for_status()
        return response

    def _post_request(self, endpoint: str, data: Dict[str, Any] = {}) -> requests.Response:
        self._ensure_token_valid()
        url: str = f'{self._base_url}{endpoint}'
        response = requests.post(url, headers=self._headers, json=data)
        response.raise_for_status()
        return response

    def _get_available_numbers(self, package_id) -> Any:
        """
         Response is a list of objects (up to 5) like {"id": "3b5a9310-5d6c-4290-0009-08dc644141f7", "phoneNumber": "0512792828", "isActive": true}
        """

        response = self._post_request(endpoint=f'Numbers/GetAvailableNumbersForPackage/{package_id}/true')
        return response.json()

    def _get_empty_esim(self, package_id: str, phone_number: str) -> Any:
        # Response is a JSON eSIM object as follows:
        # {"url": "https://codit.blob.core.windows.net/layant/esims/{uuid}.png", "id": uuid, "sim": simID, "price": 5}
        response =  self._get_request(endpoint=f'Packages/GetEmptySim/{package_id}/{phone_number}')
        return response.json()
    
    def _activate_new_line(self, price: int, package_id: str, phone_number: str, sim_number: str, customer_name: str) -> Any:
        # If the response code is 200 OK, then the eSIM was activated.
        # Additionally, will receive this message:
        # התהליך יופעל ברקע, כאשר הוא יסתיים תישלח אליך התראה.%   
        # Which means: "The process will run in the background, when it is finished you will be sent a notification"

        esim_data = {
            "Price": price,
            "Number": phone_number,
            "packageId": package_id,
            "SimNumber": sim_number,
            "Customer": {
            "Id": None,
            "IdentityNum": "",
            "Fullname": customer_name,
            "Address": "",
            "Phone": "",
            "Email": ""
            },
            "Duration": 30,
            "AutomaticRenew": False,
            "isPaid": False,
            "SaleId": None,
            "recommendedPhoneNumber": ""
        }

        response = self._post_request(
            endpoint="Deals/NewLine",
            data = esim_data
        )
        return response
    
    def _issue_esim_from_number(self, package_id: str, phone_number: str) -> Dict[str, str]:
        """Sends a request to issue esims of the specified package
        
        Args:
            package_id (str): Package ID of one of the supported packages
            phone_number (str): Specified phone number of the esim to be issued

        Returns:
            Dict[str, str]: eSIM object in the form of {"qr_code": URL, "phone_number": NUMBER}
        """
        package_price = None
        if package_id == layan_constants.WE_PACKAGE_ID:
            package_price = layan_constants.WE_PACKAGE_PRICE
        elif package_id == layan_constants.HOT_PACKAGE_ID:
            package_price = layan_constants.HOT_PACKAGE_PRICE
        else:
            print("Invalid package id")
            return 

        try:
            esim = self._get_empty_esim(package_id, phone_number)
            esim_number = esim.get("sim")
            esim_activation = self._activate_new_line(
                price=package_price,
                package_id=package_id,
                phone_number=phone_number,
                sim_number=esim_number,
                customer_name=layan_constants.CUSTOMER_NAME
            )

            return {
                "qr_code": esim.get('url'),
                "phone_number": phone_number
            }
        
        except Exception as e:
            print(f'Error issuing eSIM from number: {e}')

    def concurrently_issue_five_esims(self, package_id: str) -> List[Dict[str, str]]:
        """
        Sends a request to issue esims of the specified package, returns a list of esim dicts
        {"qr_code": URL, "phone_number": NUMBER}
        """
        try:            
            available_numbers = self._get_available_numbers(package_id)
    
            print("Available numbers:")
            print(available_numbers)

            issued_esims = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self._issue_esim_from_number, package_id=package_id, phone_number=number.get("phoneNumber")): number.get("phoneNumber") for number in available_numbers}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            issued_esims.append(result)
                    except Exception as e:
                        print(f'Failed to issue SIM card for {futures[future]}: {e}')
            
            return issued_esims
        
        except requests.exceptions.RequestException as e:
            print(f'Error in concurrent issuing of esims during the API call: {e}')
            raise
        except Exception as e:
            print(f'Unexpected error in concurrent issuing of esims: {e}')
            raise
    
        
    def batch_issue_esims(self, package_name: str,  target_count: int) -> List[Dict[str, str]]:
        """
        Issue a batch of new eSIMs that is at least as big as the given target_count.
        Batches issuances are requested in multiples of 5 at a time 
        This isn't a 100% precise function and shouldn't be used as such.
        Will break after 3 consecutive failures to issue esims and will return however many esims were issued.


        Args:
            package_name (str): Name of the restockable package (currently supports WeCom_500GB_30Days_Israel and HotMobile_110GB_30Days_Israel)

        Returns:
            List[Dict[str, str]]: eSIM objects in the form of {"qr_code": URL, "phone_number": NUMBER}
        """
        
        package_id = ""
        if package_name == "WeCom_500GB_30Days_Israel":
            package_id = layan_constants.WE_PACKAGE_ID
        elif package_name == "HotMobile_110GB_30Days_Israel":
            package_id = layan_constants.HOT_PACKAGE_ID
        else:
            print("Invalid package name")
            return []

        issued_sim_cards = []
        consecutive_failures = 0
        
        while len(issued_sim_cards) < target_count:
            # Step 1: Issue SIM cards concurrently
            issued_batch = self.concurrently_issue_five_esims(package_id)
            
            # Step 2: Check the results and update counts
            if issued_batch:
                issued_sim_cards.extend(issued_batch)
                consecutive_failures = 0
            else:
                consecutive_failures += 1

            # Step 3: Check for consecutive restocking failures
            # TODO: Use a better alerting mechanism. What is the preferred alerting framework for this condition? Preferably something that can send in Slack/Mail
            if consecutive_failures >= 3:
                print("Alarm: Three consecutive failures of issuing SIM cards.")
                break

        return issued_sim_cards