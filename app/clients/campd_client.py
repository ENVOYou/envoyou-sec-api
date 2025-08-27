import os
import requests
from dotenv import load_dotenv

load_dotenv()

class CAMDClient:
    """
    Client for interacting with the Clean Air Markets Program Data (CAMPD) API.
    This client manages requests and authentication using a dedicated API key.
    """
    def __init__(self):
        self.api_key = os.getenv("CAMPD_API_KEY")
        if not self.api_key:
            raise ValueError("CAMPD_API_KEY environment variable not set.")
        self.base_url = "https://api.epa.gov/easey"

    def get_emissions_data(self, facility_id):
        """
        Retrieves emissions data for a specific facility.

        Args:
            facility_id (int): The ID of the facility to retrieve data for.

        Returns:
            dict: A dictionary containing the emissions data, or None if the request fails.
        """
        endpoint = f"/api/v2/facilities/{facility_id}/emissions"
        headers = {
            "x-api-key": self.api_key
        }
        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching emissions data from CAMPD: {e}")
            return None

    def get_compliance_data(self, facility_id):
        """
        Retrieves compliance data for a specific facility.

        Args:
            facility_id (int): The ID of the facility to retrieve data for.

        Returns:
            dict: A dictionary containing the compliance data, or None if the request fails.
        """
        endpoint = f"/api/v2/facilities/{facility_id}/compliance"
        headers = {
            "x-api-key": self.api_key
        }
        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching compliance data from CAMPD: {e}")
            return None