"""Step definitions for: Favorable MTM Calculation (SR-IMHK-3_2_5_2-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("A clearing participant has a portfolio with market value of -300,550,000 HKD")
def step_portfolio_market_value_negative(context):
    participant = LME.Client.clearing_participant
    portfolio = LME.API.create_portfolio(participant=participant)
    portfolio.market_value = -300550000

@given("The portfolio has a contract value of -287,850,000 HKD")
def step_portfolio_contract_value_negative(context):
    portfolio.contract_value = -287850000

@given("A clearing participant has a portfolio with market value of -250,000,000 HKD")
def step_portfolio_market_value_boundary(context):
    participant = LME.Client.clearing_participant
    portfolio = LME.API.create_portfolio(participant=participant)
    portfolio.market_value = -250000000

@given("The portfolio has a contract value of -250,000,000 HKD")
def step_portfolio_contract_value_boundary(context):
    portfolio.contract_value = -250000000

@given("A clearing participant submits a portfolio for initial margin calculation")
def step_participant_submits_portfolio(context):
    participant = LME.Client.clearing_participant
    portfolio = LME.API.create_portfolio(participant=participant)

@given("The portfolio is missing the Market valuePortfolio data field")
def step_portfolio_missing_market_value(context):
    portfolio.market_value = None

@when("The system calculates Favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio")
def step_calculate_favorable_mtm(context):
    context.response = LME.API.calculate_favorable_mtm(portfolio)

@when("The system attempts to calculate Favorable MTM")
def step_attempt_calculate_favorable_mtm(context):
    context.response = LME.API.calculate_favorable_mtm(portfolio)

@then("The Favorable MTM (or MTM requirement) is calculated as -12,700,000 HKD")
def step_verify_mtm_result_negative(context):
    assert context.response.mtm_value == -12700000

@then("The negative result is identified as an MTM requirement")
def step_verify_mtm_requirement_type(context):
    assert context.response.mtm_type == 'MTM_REQUIREMENT'

@then("The favorable MTM is set to zero since the result is negative")
def step_verify_favorable_mtm_zero(context):
    assert context.response.favorable_mtm == 0

@then("The Favorable MTM (or MTM requirement) is calculated as 0 HKD")
def step_verify_mtm_zero_boundary(context):
    assert context.response.mtm_value == 0

@then("The result at the boundary is validated as neither favorable MTM nor MTM requirement")
def step_verify_boundary_exclusive(context):
    assert context.response.mtm_type == 'BOUNDARY'
    assert context.response.favorable_mtm == 0
    assert context.response.mtm_requirement == 0

@then("The calculation is rejected with a validation error")
def step_verify_validation_rejection(context):
    assert context.response.status == 'VALIDATION_ERROR'

@then("An error message indicates that Market valuePortfolio is a required field for Favorable MTM calculation")
def step_verify_missing_field_error(context):
    assert 'Market valuePortfolio' in context.response.error_message
    assert 'required' in context.response.error_message.lower()
