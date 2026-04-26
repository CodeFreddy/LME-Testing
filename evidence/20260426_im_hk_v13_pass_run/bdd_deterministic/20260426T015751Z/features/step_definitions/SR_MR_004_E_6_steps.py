"""Step definitions for: Intra-Day MTM Position Exclusion (SR-MR-004-E-6)

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then



@given("Stock positions exist that are to be settled today")
def stock_positions_exist_that_are_to_be_settled_today(context):
    # TODO: implement step: Stock positions exist that are to be settled today
    pass

@given("Positions include unposted debit, unposted credit, cash prepayment, and allocated shares")
def positions_include_unposted_debit__unposted_credit(context):
    # TODO: implement step: Positions include unposted debit, unposted credit, cash prepayment, and allocated shares
    pass

@given("A stock position with settlement date matching the collection time")
def a_stock_position_with_settlement_date_matching_the(context):
    # TODO: implement step: A stock position with settlement date matching the collection time
    pass

@given("The collection time of intra-day MTM equals the settlement obligation time")
def the_collection_time_of_intra_day_mtm_equals_the_se(context):
    # TODO: implement step: The collection time of intra-day MTM equals the settlement obligation time
    pass

@given("Stock positions include unposted debit positions")
def stock_positions_include_unposted_debit_positions(context):
    # TODO: implement step: Stock positions include unposted debit positions
    pass

@given("Stock positions include unposted credit positions")
def stock_positions_include_unposted_credit_positions(context):
    # TODO: implement step: Stock positions include unposted credit positions
    pass

@given("Stock positions include cash prepayment positions")
def stock_positions_include_cash_prepayment_positions(context):
    # TODO: implement step: Stock positions include cash prepayment positions
    pass

@given("Stock positions include allocated shares to be settled today")
def stock_positions_include_allocated_shares_to_be_set(context):
    # TODO: implement step: Stock positions include allocated shares to be settled today
    pass

@when("Intra-day MTM and margin requirement calculation is performed")
def intra_day_mtm_and_margin_requirement_calculation_i(context):
    # TODO: implement step: Intra-day MTM and margin requirement calculation is performed
    pass

@then("Positions to be settled today are excluded from the calculation")
def positions_to_be_settled_today_are_excluded_from_th(context):
    # TODO: implement step: Positions to be settled today are excluded from the calculation
    pass

@then("MTM and margin requirement are not collected from positions being settled")
def mtm_and_margin_requirement_are_not_collected_from(context):
    # TODO: implement step: MTM and margin requirement are not collected from positions being settled
    pass

@then("Position is excluded from calculation if settlement is at collection time")
def position_is_excluded_from_calculation_if_settlemen(context):
    # TODO: implement step: Position is excluded from calculation if settlement is at collection time
    pass

@then("No duplicate collection occurs for positions being settled")
def no_duplicate_collection_occurs_for_positions_being(context):
    # TODO: implement step: No duplicate collection occurs for positions being settled
    pass

@then("None of the excluded position types appear in the MTM calculation result")
def none_of_the_excluded_position_types_appear_in_the(context):
    # TODO: implement step: None of the excluded position types appear in the MTM calculation result
    pass

@then("Margin requirement calculation excludes all specified position types")
def margin_requirement_calculation_excludes_all_specif(context):
    # TODO: implement step: Margin requirement calculation excludes all specified position types
    pass
