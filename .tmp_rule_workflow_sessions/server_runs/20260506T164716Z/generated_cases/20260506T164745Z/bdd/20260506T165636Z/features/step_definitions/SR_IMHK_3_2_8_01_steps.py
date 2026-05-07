"""Step definitions for: Total MTM and Margin Requirement Calculation (SR-IMHK-3_2_8-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("net margin after credit is {amount:d}")
def step_set_net_margin_after_credit(context):
    LME.API.set_margin_component('net_margin_after_credit', amount)

@given("MTM requirement is {amount:d}")
def step_set_mtm_requirement(context):
    LME.API.set_margin_component('mtm_requirement', amount)

@given("position limit add-on is {amount:d}")
def step_set_position_limit_addon(context):
    LME.API.set_margin_component('position_limit_addon', amount)

@given("credit risk add-on is {amount:d}")
def step_set_credit_risk_addon(context):
    LME.API.set_margin_component('credit_risk_addon', amount)

@given("credit risk add-on is {amount:d} (not applicable after VaR Platform launch)")
def step_set_credit_risk_addon_var_platform(context):
    LME.API.set_margin_component('credit_risk_addon', amount)

@given("ad-hoc add-on is {amount:d}")
def step_set_adhoc_addon(context):
    LME.API.set_margin_component('adhoc_addon', amount)

@given("MTM requirement is missing or null")
def step_set_mtm_requirement_missing(context):
    LME.API.set_margin_component('mtm_requirement', None)

@when("the system calculates total MTM and margin requirement")
def step_calculate_total_mtm_margin(context):
    result = LME.API.calculate_total_mtm_margin()

@when("the system attempts to calculate total MTM and margin requirement")
def step_attempt_calculate_total_mtm_margin(context):
    result = LME.API.calculate_total_mtm_margin(expect_error=True)

@then("total MTM and margin requirement equals {expected:d}")
def step_verify_total_mtm_margin(context):
    assert result.total_mtm_margin_requirement == expected

@then("the calculation is rejected with a validation error indicating missing MTM requirement")
def step_verify_validation_error(context):
    assert result.error is not None
    assert 'MTM requirement' in result.error_message
