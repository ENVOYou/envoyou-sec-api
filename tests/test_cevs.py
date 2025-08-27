from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


def test_compute_cevs_for_company_basic():
    company_name = "Test Company"
    response = client.get(f"/global/cevs/{company_name}")
    assert response.status_code == 200
    data = response.json()
    assert "score" in data and isinstance(data["score"], float)
    assert "components" in data
    assert "sources" in data
    assert "details" in data


def test_compute_cevs_for_company_with_country():
    company_name = "Test Company"
    country = "Sweden"
    response = client.get(f"/global/cevs/{company_name}?company_country={country}")
    assert response.status_code == 200
    data = response.json()
    sources = data.get("sources", {})
    assert "edgar_source" in sources
    assert "renewables_source" in sources
    assert "pollution_trend_source" in sources


@pytest.mark.parametrize("pollution_source_val,expected", [
    ("edgar", "edgar"),
    ("auto", ("auto", "eea", "edgar")),
])
def test_env_switch_pollution_source(monkeypatch, pollution_source_val, expected):
    monkeypatch.setenv("CEVS_POLLUTION_SOURCE", pollution_source_val)
    country = "United States" if pollution_source_val == "edgar" else "Austria"
    response = client.get(f"/global/cevs/Test Company?company_country={country}")
    assert response.status_code == 200
    data = response.json()
    result = data["sources"].get("pollution_trend_source")
    if isinstance(expected, tuple):
        assert result in expected
    else:
        assert result == expected


def test_sweden_renewable_bonus_scenario():
    response = client.get("/global/cevs/Swedish Green Tech AB?company_country=Sweden")
    assert response.status_code == 200
    data = response.json()
    details = data["details"]
    renewables = details.get("renewables", {})
    if renewables.get("country_row"):
        country_data = renewables["country_row"]
        share_2021 = country_data.get("renewable_energy_share_2021_proxy")
        target_2020 = country_data.get("target_2020")
        if isinstance(share_2021, (int, float)) and isinstance(target_2020, (int, float)):
            assert share_2021 > target_2020
            components = data["components"]
            renewable_bonus = components.get("renewables_bonus", 0)
            assert renewable_bonus > 0
def test_pollution_penalty_variation():
    res_germany = client.get("/global/cevs/German Industrial Corp?company_country=Germany")
    res_poland = client.get("/global/cevs/Polish Manufacturing Ltd?company_country=Poland")
    assert res_germany.status_code == 200
    assert res_poland.status_code == 200
    components_de = res_germany.json()["components"]
    components_pl = res_poland.json()["components"]
    pollution_penalty_de = abs(components_de.get("pollution_penalty", 0))
    pollution_penalty_pl = abs(components_pl.get("pollution_penalty", 0))
    assert "pollution_penalty" in components_de
    assert "pollution_penalty" in components_pl
    assert components_de["pollution_penalty"] <= 0
    assert components_pl["pollution_penalty"] <= 0


def test_austria_policy_bonus_scenario():
    response = client.get("/global/cevs/Austrian ISO Certified Corp?company_country=Austria")
    assert response.status_code == 200
    data = response.json()
    sources = data["sources"]
    details = data["details"]
    assert "policy_source" in sources
    assert "policy" in details
    policy_details = details["policy"]
    assert isinstance(policy_details, dict)


def test_component_balance_and_constraints():
    response = client.get("/global/cevs/Test Balanced Corp?company_country=Germany")
    assert response.status_code == 200
    data = response.json()
    components = data["components"]
    score = data["score"]
    expected_score = (
        components["base"] + 
        components["iso_bonus"] + 
        components["epa_penalty"] + 
        components["renewables_bonus"] + 
        components["pollution_penalty"] + 
        components["policy_bonus"]
    )
    clamped_score = max(0.0, min(100.0, expected_score))
    assert abs(score - clamped_score) < 0.01, f"Score {score} should match component sum {clamped_score}"
    assert components["base"] == 50.0
    assert 0 <= components["iso_bonus"] <= 30
    assert -30 <= components["epa_penalty"] <= 0
    assert 0 <= components["renewables_bonus"] <= 20
    assert -15 <= components["pollution_penalty"] <= 0
    assert 0 <= components["policy_bonus"] <= 3
    
def test_data_source_consistency():
    response = client.get("/global/cevs/Source Test Corp?company_country=Finland")
    assert response.status_code == 200
    data = response.json()
    sources = data["sources"]
    required_sources = [
        "epa_matches", "iso_count", "renewables_source", 
        "pollution_source", "edgar_source", "policy_source", 
        "pollution_trend_source"
    ]
    for source_key in required_sources:
        assert source_key in sources, f"Missing source key: {source_key}"
    assert isinstance(sources["epa_matches"], int) and sources["epa_matches"] >= 0
    assert isinstance(sources["iso_count"], int) and sources["iso_count"] >= 0
    source_descriptions = ["renewables_source", "pollution_source", "edgar_source", "policy_source"]
    for desc_key in source_descriptions:
        assert isinstance(sources[desc_key], str) and len(sources[desc_key]) > 0

