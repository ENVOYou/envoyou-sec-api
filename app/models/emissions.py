"""
Pydantic Models for Standardized Emissions Data
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class StandardizedEmission(BaseModel):
    """Represents a single, standardized emissions data point from any source."""
    facility_name: Optional[str] = Field(None, description="Name of the facility or power plant.")
    state: str = Field(..., description="Two-letter state code.")
    year: int = Field(..., description="Year the data was recorded.")
    pollutant: str = Field(..., description="Type of pollutant (e.g., 'CO2', 'NOx').")
    emissions: float = Field(..., description="Amount of emissions.")
    unit: str = Field(..., description="Unit of measurement for emissions (e.g., 'tons').")
    source: str = Field(..., description="The original data source (e.g., 'EPA', 'EIA').")
    raw_data_id: Optional[str] = Field(None, description="Original ID from the source system.")


class StandardizedEmissionsResponse(BaseModel):
    """A standardized response container for a list of emissions data."""
    source: str
    data: List[StandardizedEmission]
