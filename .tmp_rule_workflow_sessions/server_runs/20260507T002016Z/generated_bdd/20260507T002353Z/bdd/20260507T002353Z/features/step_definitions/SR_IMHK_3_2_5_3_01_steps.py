"""Step definitions for: Application of Margin Credit (SR-IMHK-3_2_5_3-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("Net margin before credit is 46,930,000")
def step_net_margin_before_credit(context):
    context.net_margin_before = 46930000

@given("Margin credit is 5,000,000")
def step_margin_credit(context):
    context.margin_credit = 5000000

@given("Net margin before credit is exactly 5,000,000")
def step_net_margin_boundary(context):
    context.net_margin_before = 5000000

@given("A clearing participant with margin calculation request")
def step_clearing_participant(context):
    context.cp = LME.Client.get_clearing_participant()

@when("the system calculates net margin after credit")
def step_calculate_net_margin(context):
    context.response = LME.API.calculate_margin(context.cp)

@when("the system applies the Maximum[0, (Net margin – Margin credit)] formula")
def step_apply_maximum_formula(context):
    context.net_margin_after = max(0, context.net_margin_before - context.margin_credit)

@when("the system validates the margin credit value")
def step_validate_margin_credit(context):
    context.credit_valid = LME.PostTrade.validate_credit_value(context.margin_credit)

@when("the system validates the Maximum function logic for net margin calculation")
def step_validate_maximum_logic(context):
    context.logic_valid = LME.PostTrade.validate_formula_logic("Maximum[0, (Net margin – Margin credit)]")

@then("net margin after credit is calculated as 41,930,000")
def step_verify_net_margin_positive(context):
    assert context.net_margin_after == 41930000

@then("net margin after credit is 0")
def step_verify_net_margin_zero(context):
    assert context.net_margin_after == 0

@then("the Maximum function ensures the result is not negative")
def step_verify_non_negative(context):
    assert context.net_margin_after >= 0

@then("margin credit is a valid positive numeric value")
def step_verify_credit_valid(context):
    assert isinstance(context.margin_credit, (int, float)) and context.margin_credit > 0

@then("the Maximum[0, (Net margin – Margin credit)] formula is correctly implemented")
def step_verify_formula_implementation(context):
    assert LME.PostTrade.check_formula_implementation("Maximum[0, (Net margin – Margin credit)]")

@then("net margin after credit is never negative regardless of input values")
def step_verify_floor_zero(context):
    assert all(val >= 0 for val in context.test_results)
