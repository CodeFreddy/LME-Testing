"""Step definitions for: Rounding on Aggregated Market-risk-component Margin (SR-IMHK-3_2_5_1-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("A clearing participant has market risk components with Portfolio margin = 10,000,000")
def step_portfolio_margin(context):
    participant = LME.Client.clearing_participant
    participant.set_market_risk_component('portfolio_margin', 10000000)

@given("Flat rate margin = 15,180,000")
def step_flat_rate_margin(context):
    participant = LME.Client.clearing_participant
    participant.set_market_risk_component('flat_rate_margin', 15180000)

@given("Liquidation risk add-on = 266,865")
def step_liquidation_risk_addon(context):
    participant = LME.Client.clearing_participant
    participant.set_market_risk_component('liquidation_risk_addon', 266865)

@given("Structured product add-on = 550,000")
def step_structured_product_addon(context):
    participant = LME.Client.clearing_participant
    participant.set_market_risk_component('structured_product_addon', 550000)

@given("Corporate action position margin = 2,500,000")
def step_corporate_action_margin(context):
    participant = LME.Client.clearing_participant
    participant.set_market_risk_component('corporate_action_position_margin', 2500000)

@given("Holiday add-on = 18,433,039")
def step_holiday_addon(context):
    participant = LME.Client.clearing_participant
    participant.set_market_risk_component('holiday_addon', 18433039)

@given("The Initial Margin Risk Parameter File specifies a rounding parameter of 10,000")
def step_rounding_parameter(context):
    LME.API.set_risk_parameter('rounding_parameter', 10000)

@given("A clearing participant has market risk components that sum to exactly 46,930,000")
def step_exact_boundary_sum(context):
    participant = LME.Client.clearing_participant
    participant.set_aggregated_margin(46930000)

@given("A clearing participant has market risk components with values for Portfolio margin, Flat rate margin, Liquidation risk add-on, Structured product add-on, Corporate action position margin, and Holiday add-on")
def step_all_risk_components(context):
    participant = LME.Client.clearing_participant
    participant.initialize_all_market_risk_components()

@given("The Initial Margin Risk Parameter File contains a rounding parameter")
def step_rounding_parameter_exists(context):
    LME.API.load_risk_parameter_file()

@when("The system calculates the aggregated market-risk-component margin and applies rounding")
def step_calculate_and_round(context):
    global response
    context.response = LME.PostTrade.calculate_aggregated_margin(apply_rounding=True)

@when("The system rounds up the aggregated margin to the nearest 10,000")
def step_round_aggregated_margin(context):
    global response
    context.response = LME.PostTrade.round_aggregated_margin(rounding_unit=10000)

@when("The system calculates the aggregated market-risk-component margin")
def step_calculate_aggregated(context):
    global response
    context.response = LME.PostTrade.calculate_aggregated_margin(apply_rounding=False)

@then("The aggregated margin is calculated as 46,929,904")
def step_verify_calculation(context):
    assert context.response.raw_aggregated_margin == 46929904

@then("The aggregated margin is rounded up to 46,930,000")
def step_verify_rounding(context):
    assert context.response.rounded_aggregated_margin == 46930000

@then("The rounded aggregated market-risk-component margin remains 46,930,000")
def step_verify_boundary_rounding(context):
    assert context.response.rounded_aggregated_margin == 46930000

@then("All six components are summed in the correct formula order")
def step_verify_formula_order(context):
    expected_formula = ['portfolio_margin', 'flat_rate_margin', 'liquidation_risk_addon', 'structured_product_addon', 'corporate_action_position_margin', 'holiday_addon']
    assert context.response.formula_components == expected_formula

@then("The rounding parameter from the Initial Margin Risk Parameter File is retrieved and applied to round up the aggregated margin")
def step_verify_rounding_parameter_applied(context):
    assert context.response.rounding_parameter_source == 'Initial_Margin_Risk_Parameter_File'
    assert context.response.rounding_applied == True
