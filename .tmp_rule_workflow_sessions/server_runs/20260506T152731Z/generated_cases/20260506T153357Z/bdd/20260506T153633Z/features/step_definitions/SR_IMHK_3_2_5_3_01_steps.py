"""Step definitions for: Application of Margin Credit (SR-IMHK-3_2_5_3-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("a clearing participant has a net margin of {net_margin} HKD")
def step_clearing_participant_net_margin(context):
    participant = LME.Client.clearing_participant()
    participant.net_margin = float(net_margin.replace(',', ''))

@given("the margin credit granted is {margin_credit} HKD")
def step_margin_credit_granted(context):
    participant.margin_credit = float(margin_credit.replace(',', ''))

@given("a clearing participant is registered in the system")
def step_clearing_participant_registered(context):
    global participant
    participant = LME.Client.register_clearing_participant()

@given("the standard margin credit value is {margin_credit} HKD")
def step_standard_margin_credit(context):
    LME.API.set_standard_margin_credit(float(margin_credit.replace(',', '')))

@when("the system calculates net margin after credit using the formula Maximum[0, (Net margin - Margin credit)]")
def step_calculate_net_margin_after_credit(context):
    global result
    result = LME.PostTrade.calculate_net_margin_after_credit(participant)

@when("the subtraction result equals zero")
def step_subtraction_equals_zero(context):
    assert participant.net_margin == participant.margin_credit

@when("the system applies margin credit for margin calculation")
def step_apply_margin_credit(context):
    global result
    result = LME.API.apply_margin_credit(participant)

@then("net margin after credit is calculated as {expected_value}")
def step_verify_net_margin_after_credit(context):
    expected = float(expected_value.replace('Maximum[0, (46,930,000 - 5,000,000)] = ', '').replace(',', ''))
    assert result.net_margin_after_credit == expected

@then("the margin credit of {margin_credit} is granted to the clearing participant")
def step_verify_margin_credit_granted(context):
    expected = float(margin_credit.replace(',', ''))
    assert participant.granted_margin_credit == expected

@then("the margin credit is applied in the net margin after credit calculation")
def step_verify_margin_credit_applied(context):
    assert result.margin_credit_applied == True
