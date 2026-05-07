"""Step definitions for: Total MTM and Margin Requirement Calculation (SR-IMHK-3_2_8-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("net margin after credit is calculated as {value}")
def step_set_net_margin_after_credit(context):
    global risk_components
    risk_components = LME.PostTrade.RiskComponents()
    risk_components.net_margin_after_credit = float(value.replace(',', ''))

@given("MTM requirement is {value}")
def step_set_mtm_requirement(context):
    risk_components.mtm_requirement = float(value.replace(',', ''))

@given("position limit add-on is {value}")
def step_set_position_limit_addon(context):
    risk_components.position_limit_addon = float(value.replace(',', ''))

@given("credit risk add-on is {value}")
def step_set_credit_risk_addon(context):
    risk_components.credit_risk_addon = float(value.replace(',', ''))

@given("credit risk add-on is not applicable due to VaR Platform launch")
def step_credit_risk_addon_not_applicable(context):
    risk_components.credit_risk_addon = 0.0
    risk_components.credit_risk_applicable = False

@given("ad-hoc add-on is {value}")
def step_set_adhoc_addon(context):
    risk_components.adhoc_addon = float(value.replace(',', ''))

@given("a clearing participant has positions requiring margin calculation")
def step_participant_has_positions(context):
    global participant
    participant = LME.Client.clearing_participant_with_positions()

@given("results from §3.2.5 and §3.2.6 calculations are available")
def step_prior_calculations_available(context):
    global risk_components
    risk_components = LME.API.get_prior_calculation_results(participant)

@when("the system derives total MTM and margin requirement by adding net margin after credit to other risk components")
def step_calculate_total_mtm(context):
    global result
    result = LME.PostTrade.calculate_total_mtm_margin_requirement(risk_components)

@when("the system derives total MTM and margin requirement with credit risk add-on set to zero")
def step_calculate_total_mtm_no_credit_risk(context):
    global result
    result = LME.PostTrade.calculate_total_mtm_margin_requirement(risk_components, exclude_credit_risk=True)

@when("the system validates that all required components are present: {component_list}")
def step_validate_components_present(context):
    global validation_result
    context.validation_result = LME.API.validate_risk_components(risk_components)

@then("total MTM and margin requirement equals {expected_total}")
def step_verify_total_mtm(context):
    expected = float(expected_total.replace(',', ''))
    assert result.total_mtm_margin_requirement == expected

@then("total MTM and margin requirement equals {expected_total} (excluding credit risk add-on)")
def step_verify_total_mtm_excluding_credit_risk(context):
    expected = float(expected_total.replace(',', ''))
    assert result.total_mtm_margin_requirement == expected
    assert result.credit_risk_excluded == True

@then("validation confirms all components are present with valid numeric format")
def step_verify_components_valid(context):
    assert context.validation_result.all_present == True
    assert context.validation_result.all_numeric == True

@then("calculation proceeds to derive total MTM and margin requirement")
def step_calculation_proceeds(context):
    assert context.validation_result.can_proceed == True
