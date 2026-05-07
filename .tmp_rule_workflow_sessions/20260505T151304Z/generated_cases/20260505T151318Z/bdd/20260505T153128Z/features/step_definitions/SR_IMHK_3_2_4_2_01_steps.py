"""Step definitions for: Flat Rate Margin Calculation (SR-IMHK-3_2_4_2-01)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("a clearing participant has positions across multiple sub-margin groups")
def step_participant_multiple_subgroups(context):
    participant = LME.Client.clearing_participant()
    LME.API.setup_positions(participant, sub_margin_groups=['sub_group_1', 'sub_group_2', 'sub_group_3'])

@given("sub-group 1 has long positions with total absolute market value of {long_value_1} HKD and short positions with total absolute market value of {short_value_1} HKD")
def step_subgroup1_positions(context):
    LME.API.set_subgroup_positions('sub_group_1', long_value=float(long_value_1.replace(',', '')), short_value=float(short_value_1.replace(',', '')))

@given("sub-group 2 has long positions with total absolute market value of {long_value_2} HKD and no short positions")
def step_subgroup2_positions(context):
    LME.API.set_subgroup_positions('sub_group_2', long_value=float(long_value_2.replace(',', '')), short_value=0)

@given("sub-group 3 has no long positions and short positions with total absolute market value of {short_value_3} HKD")
def step_subgroup3_positions(context):
    LME.API.set_subgroup_positions('sub_group_3', long_value=0, short_value=float(short_value_3.replace(',', '')))

@given("flat margin rates are defined under FieldType 3")
def step_flat_margin_rates(context):
    rates = LME.API.get_flat_margin_rates(field_type=3)
    LME.API.configure_margin_rates(rates)

@given("a flat rate margin multiplier of {multiplier} is assigned per DWH0081C report")
def step_margin_multiplier(context):
    LME.API.set_margin_multiplier(source='DWH0081C', multiplier=float(multiplier))

@given("a clearing participant has positions in a sub-margin group")
def step_participant_single_subgroup(context):
    participant = LME.Client.clearing_participant()
    LME.API.setup_positions(participant, sub_margin_groups=['sub_group_1'])

@given("the total absolute market value of long positions equals the total absolute market value of short positions")
def step_equal_long_short_values(context):
    LME.API.set_subgroup_positions('sub_group_1', long_value=50000000, short_value=50000000)

@given("a flat rate margin multiplier is assigned per DWH0081C report")
def step_margin_multiplier_assigned(context):
    multiplier = LME.API.get_margin_multiplier(source='DWH0081C')
    LME.API.set_margin_multiplier(source='DWH0081C', multiplier=multiplier)

@given("a clearing participant submits position data for flat rate margin calculation")
def step_submit_position_data(context):
    participant = LME.Client.clearing_participant()
    LME.API.prepare_position_submission(participant)

@given("position data includes instrument IDs, quantities, and market values")
def step_position_data_fields(context):
    LME.API.set_position_fields(['instrument_id', 'quantity', 'market_value'])

@when("the flat rate margin calculation is performed")
def step_perform_flat_rate_margin(context):
    global response
    context.response = LME.PostTrade.calculate_flat_rate_margin()

@when("the flat rate margin calculation is performed for this sub-margin group")
def step_perform_flat_rate_margin_subgroup(context):
    global response
    context.response = LME.PostTrade.calculate_flat_rate_margin(sub_margin_group='sub_group_1')

@when("the submitted position data is missing required fields such as {missing_fields}")
def step_missing_required_fields(context):
    global response
    context.response = LME.API.submit_position_data(missing_fields=missing_fields.split(', '))

@then("the system includes only {position_type} positions for sub-group {group_id} (higher absolute market value)")
def step_verify_included_positions(context):
    included = context.response.get_included_positions(group_id)
    assert included['position_type'] == position_type

@then("the flat rate margin is calculated as {expected_value} HKD")
def step_verify_flat_rate_margin(context):
    expected = float(expected_value.replace(',', ''))
    assert context.response.flat_rate_margin == expected

@then("the system determines which positions to include based on the tie-breaking rule when long and short absolute market values are equal")
def step_verify_tie_breaking(context):
    assert context.response.tie_breaking_applied == True
    assert context.response.included_position_type in ['long', 'short', 'both', 'neither']

@then("the flat rate margin calculation proceeds with the determined position set")
def step_verify_calculation_proceeds(context):
    assert context.response.calculation_completed == True

@then("the system rejects the calculation request")
def step_verify_rejection(context):
    assert context.response.status == 'rejected'

@then("an appropriate validation error is returned indicating the missing or invalid required fields")
def step_verify_validation_error(context):
    assert context.response.error_code == 'VALIDATION_ERROR'
    assert len(context.response.missing_fields) > 0
