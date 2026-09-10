from app.services.scenario_service import get_all_scenarios, get_scenario_by_code

def test_12_predefined_scenarios():
    scenarios = get_all_scenarios()
    assert len(scenarios) == 12
    
    expected_codes = [
        "NORMAL_GENUINE_ACTIVITY",
        "HIGH_VALUE_GENUINE_TRANSACTION",
        "NEW_DEVICE_GENUINE_USER",
        "NEW_LOCATION_GENUINE_USER",
        "MULE_FAN_IN",
        "MULE_FAN_OUT",
        "MULTI_HOP_MULE_NETWORK",
        "MULE_TO_GENUINE",
        "ACCOUNT_TAKEOVER",
        "CROSS_BANK_MULE_NETWORK",
        "MIXED_NETWORK",
        "CUSTOM_SCENARIO"
    ]
    
    actual_codes = [s.scenario_code for s in scenarios]
    for code in expected_codes:
        assert code in actual_codes
        sc = get_scenario_by_code(code)
        assert sc is not None
        assert sc.description != ""
        assert sc.target_hypothesis != ""
