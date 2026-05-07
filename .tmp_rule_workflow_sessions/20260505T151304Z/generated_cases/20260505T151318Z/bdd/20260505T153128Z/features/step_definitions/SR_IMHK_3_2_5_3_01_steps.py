"""Step definitions for: Application of Margin Credit (SR-IMHK-3_2_5_3-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("A clearing participant has a net margin of 46,930,000")
def step_cp_has_net_margin_46930000(context):
    cp = LME.Client.clearing_participant
    LME.API.set_net_margin(cp, 46930000)

@given("A margin credit of 5,000,000 is granted to the clearing participant")
def step_margin_credit_granted(context):
    cp = LME.Client.clearing_participant
    LME.API.grant_margin_credit(cp, 5000000)

@given("A clearing participant has a net margin of 5,000,000")
def step_cp_has_net_margin_5000000(context):
    cp = LME.Client.clearing_participant
    LME.API.set_net_margin(cp, 5000000)

@given("A clearing participant is registered in the system")
def step_cp_registered(context):
    cp = LME.Client.register_clearing_participant()

@when("The margin credit is applied for margin calculation")
def step_apply_margin_credit(context):
    global response
    context.response = LME.PostTrade.apply_margin_credit()

@then("The net margin after credit is calculated as 41,930,000")
def step_verify_net_margin_41930000(context):
    assert context.response.net_margin_after_credit == 41930000

@then("The net margin after credit is calculated as 0")
def step_verify_net_margin_zero(context):
    assert context.response.net_margin_after_credit == 0

@then("The margin credit value is validated as 5,000,000")
def step_validate_margin_credit_value(context):
    assert context.response.margin_credit_value == 5000000

@then("The margin credit is granted to the clearing participant")
def step_verify_margin_credit_granted(context):
    assert context.response.margin_credit_granted == True
