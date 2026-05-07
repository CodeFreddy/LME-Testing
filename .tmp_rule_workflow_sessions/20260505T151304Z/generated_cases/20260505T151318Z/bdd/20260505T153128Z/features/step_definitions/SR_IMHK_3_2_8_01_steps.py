"""Step definitions for: Total MTM and Margin Requirement Calculation (SR-IMHK-3_2_8-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("Net margin after credit value is available (e.g., {net_margin_after_credit})")
def step_net_margin_after_credit_available(context):
    LME.API.set_margin_component('net_margin_after_credit', float(net_margin_after_credit.replace(',', '')))

@given("MTM requirement value is available (e.g., {mtm_requirement})")
def step_mtm_requirement_available(context):
    LME.API.set_margin_component('mtm_requirement', float(mtm_requirement.replace(',', '')))

@given("Position limit add-on value is available (e.g., {position_limit_addon})")
def step_position_limit_addon_available(context):
    LME.API.set_margin_component('position_limit_addon', float(position_limit_addon.replace(',', '')))

@given("Credit risk add-on value is available (e.g., {credit_risk_addon})")
def step_credit_risk_addon_available(context):
    LME.API.set_margin_component('credit_risk_addon', float(credit_risk_addon.replace(',', '')))

@given("Ad-hoc add-on value is available (e.g., {adhoc_addon})")
def step_adhoc_addon_available(context):
    LME.API.set_margin_component('adhoc_addon', float(adhoc_addon.replace(',', '')))

@given("VaR Platform has been launched")
def step_var_platform_launched(context):
    LME.API.set_platform_status('VaR', launched=True)
    LME.API.set_margin_component('credit_risk_addon', 0)

@given("Credit risk add-on is not applicable (value is 0)")
def step_credit_risk_addon_not_applicable(context):
    LME.API.set_margin_component('credit_risk_addon', 0)
    LME.API.set_component_applicability('credit_risk_addon', False)

@given("All other risk components have valid values")
def step_all_other_components_valid(context):
    LME.API.set_margin_component('net_margin_after_credit', 41930000)
    LME.API.set_margin_component('mtm_requirement', 12700000)
    LME.API.set_margin_component('position_limit_addon', 487332)
    LME.API.set_margin_component('adhoc_addon', 600000)

@given("One or more margin component values are missing or null")
def step_margin_components_missing(context):
    LME.API.clear_margin_components()
    LME.API.set_margin_component('net_margin_after_credit', None)

@given("The calculation request is submitted for total MTM and margin requirement")
def step_calculation_request_submitted(context):
    global calculation_request
    calculation_request = LME.API.create_margin_calculation_request()

@when("The system derives total MTM and margin requirement")
def step_system_derives_total_mtm_margin(context):
    global calculation_result
    calculation_result = LME.API.calculate_total_mtm_margin_requirement()

@when("The system attempts to derive total MTM and margin requirement")
def step_system_attempts_derive_total_mtm_margin(context):
    global calculation_result, validation_error
    try:
        calculation_result = LME.API.calculate_total_mtm_margin_requirement()
        validation_error = None
    except LME.API.ValidationError as e:
        validation_error = e
        calculation_result = None

@then("Total MTM and margin requirement equals the sum of all components (e.g., {expected_total})")
def step_total_equals_sum(context):
    expected = float(expected_total.replace(',', ''))
    actual = calculation_result['total_mtm_margin_requirement']
    assert abs(actual - expected) < 0.01, f"Expected {expected}, got {actual}"

@then("Total MTM and margin requirement equals the sum of all applicable components excluding credit risk add-on")
def step_total_excludes_credit_risk_addon(context):
    components = LME.API.get_margin_components()
    expected = (components['net_margin_after_credit'] + 
                components['mtm_requirement'] + 
                components['position_limit_addon'] + 
                components['adhoc_addon'])
    actual = calculation_result['total_mtm_margin_requirement']
    assert abs(actual - expected) < 0.01, f"Expected {expected}, got {actual}"

@then("The calculation is rejected")
def step_calculation_rejected(context):
    assert calculation_result is None, "Calculation should be rejected"
    assert validation_error is not None, "Validation error should be raised"

@then("An appropriate validation error is returned indicating missing or invalid component data")
def step_validation_error_returned(context):
    assert validation_error is not None, "Validation error should be present"
    assert 'missing' in str(validation_error).lower() or 'invalid' in str(validation_error).lower(), \
        f"Error message should indicate missing or invalid data: {validation_error}"
