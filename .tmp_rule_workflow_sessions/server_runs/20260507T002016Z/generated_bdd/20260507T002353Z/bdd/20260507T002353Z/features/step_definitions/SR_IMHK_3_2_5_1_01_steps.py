"""Step definitions for: Rounding on Aggregated Market-risk-component Margin (SR-IMHK-3_2_5_1-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("Portfolio margin is 10,000,000")
def step_portfolio_margin(context):
    LME.API.set_margin_component(component="portfolio_margin", value=10000000)

@given("Flat rate margin is 15,180,000")
def step_flat_rate_margin(context):
    LME.API.set_margin_component(component="flat_rate_margin", value=15180000)

@given("Liquidation risk add-on is 266,865")
def step_liquidation_risk(context):
    LME.API.set_margin_component(component="liquidation_risk_addon", value=266865)

@given("Structured product add-on is 550,000")
def step_structured_product(context):
    LME.API.set_margin_component(component="structured_product_addon", value=550000)

@given("Corporate action position margin is 2,500,000")
def step_corporate_action(context):
    LME.API.set_margin_component(component="corporate_action_margin", value=2500000)

@given("Holiday add-on is 18,433,039")
def step_holiday_addon(context):
    LME.API.set_margin_component(component="holiday_addon", value=18433039)

@given("Rounding parameter in Initial Margin Risk Parameter File is 10,000")
def step_rounding_param(context):
    LME.Client.load_risk_parameters(rounding_unit=10000)

@given("Aggregated margin before rounding is exactly 46,930,000")
def step_exact_aggregated_margin(context):
    LME.API.set_margin_component(component="aggregated_margin_raw", value=46930000)

@given("A clearing participant portfolio with margin calculation request")
def step_portfolio_request(context):
    LME.Client.initiate_margin_calculation(portfolio_id="TEST_PORTFOLIO")

@when("the clearing participant calculates the aggregated market-risk-component margin")
def step_calculate_aggregated_margin(context):
    LME.PostTrade.calculate_aggregated_margin()

@when("the system applies rounding up to the nearest 10,000")
def step_apply_rounding(context):
    LME.API.apply_rounding(rounding_unit=10000, direction="up")

@when("the system validates the presence of all margin components")
def step_validate_components(context):
    LME.API.validate_margin_components(required=["portfolio", "flat_rate", "liquidation", "structured", "corporate_action", "holiday"])

@when("the system validates the rounding parameter from the Initial Margin Risk Parameter File")
def step_validate_rounding_param(context):
    LME.Client.validate_risk_parameter("rounding_unit")

@then("the aggregated margin before rounding is calculated as 46,929,904")
def step_verify_raw_margin(context):
    assert LME.API.get_margin_result("aggregated_raw") == 46929904

@then("the rounded aggregated market-risk-component margin is 46,930,000")
def step_verify_rounded_margin(context):
    assert LME.API.get_margin_result("aggregated_rounded") == 46930000

@then("the rounded aggregated market-risk-component margin remains 46,930,000")
def step_verify_boundary_margin(context):
    assert LME.API.get_margin_result("aggregated_rounded") == 46930000

@then("no upward adjustment is applied since value is already at the rounding boundary")
def step_verify_no_adjustment(context):
    assert LME.API.get_adjustment_log() == []

@then("Portfolio margin is present and valid")
def step_validate_portfolio_margin(context):
    assert LME.API.check_component_status("portfolio_margin") == "valid"

@then("Flat rate margin is present and valid")
def step_validate_flat_rate(context):
    assert LME.API.check_component_status("flat_rate_margin") == "valid"

@then("Liquidation risk add-on is present and valid")
def step_validate_liquidation(context):
    assert LME.API.check_component_status("liquidation_risk_addon") == "valid"

@then("Structured product add-on is present and valid")
def step_validate_structured(context):
    assert LME.API.check_component_status("structured_product_addon") == "valid"

@then("Corporate action position margin is present and valid")
def step_validate_corporate_action(context):
    assert LME.API.check_component_status("corporate_action_margin") == "valid"

@then("Holiday add-on is present and valid")
def step_validate_holiday(context):
    assert LME.API.check_component_status("holiday_addon") == "valid"

@then("Rounding parameter is retrieved from the Initial Margin Risk Parameter File")
def step_verify_param_retrieval(context):
    assert LME.Client.get_risk_parameter("rounding_unit") is not None
