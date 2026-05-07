"""Step definitions for: Application of Margin Credit (SR-IMHK-3_2_5_3-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("a clearing participant with net margin of {net_margin:d}")
def step_cp_with_net_margin(context):
    cp = LME.Client.clearing_participant()
    LME.API.set_margin_state(cp, net_margin=net_margin)

@given("margin credit of {margin_credit:d} granted to the CP")
def step_margin_credit_granted(context):
    LME.API.set_margin_credit(cp, amount=margin_credit)

@given("a clearing participant registered in the system")
def step_cp_registered(context):
    cp = LME.Client.register_clearing_participant()

@when("the system calculates net margin after credit using Maximum[0, (Net margin – Margin credit)]")
def step_calculate_net_margin_after_credit(context):
    result = LME.API.calculate_margin_after_credit(cp)

@when("the system validates margin credit assignment for the CP")
def step_validate_margin_credit(context):
    validation = LME.API.validate_margin_credit_assignment(cp)

@then("net margin after credit equals {expected:d}")
def step_verify_net_margin_after_credit(context):
    assert result.net_margin_after_credit == expected

@then("margin credit is granted to each CP")
def step_verify_margin_credit_granted(context):
    assert validation.margin_credit_granted == True

@then("margin credit value is normally {amount:d}")
def step_verify_margin_credit_value(context):
    assert validation.margin_credit_amount == amount

@then("margin credit is applied for margin calculation")
def step_verify_margin_credit_applied(context):
    assert validation.margin_credit_applied == True
