"""
Pydantic models for standardized data from external APIs.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List

class AirQualityCategory(BaseModel):
    """Describes the air quality category (e.g., Good, Moderate)."""
    name: str = Field(..., alias="Name", description="The category name.")

class AirQualityData(BaseModel):
    """A standardized model for air quality observations."""
    reporting_area: str = Field(..., alias="ReportingArea", description="The area for which the AQI is reported.")
    aqi: int = Field(..., alias="AQI", description="The Air Quality Index value.")
    category: AirQualityCategory = Field(..., alias="Category", description="The AQI category.")

    model_config = ConfigDict(populate_by_name=True)
