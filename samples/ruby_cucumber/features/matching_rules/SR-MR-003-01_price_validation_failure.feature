Feature: Price Validation Failure Contact Obligation
  SR-MR-003-01
  Validates that Members contact the Exchange when orders/trades fail price validation

  @positive @post_trade
  Scenario: Member contacts Exchange after price validation failure
    Given an order or trade fails the price validation check
    When the Member contacts the Exchange to explain the rationale for the price
    Then the processing result indicates compliance

  @negative @post_trade
  Scenario: Member fails to contact Exchange after price validation failure
    Given an order or trade fails the price validation check
    When the Member does not contact the Exchange to explain the rationale for the price
    Then the processing result indicates non-compliance or failure

  @boundary @post_trade
  Scenario: Trade re-submission after providing additional information
    Given trade submission resulted in Failed Checks
    And Exchange requested additional information
    And Member provided the requested additional information
    When Member requests to re-submit the trade in its original form
    Then system permits the trade re-submission
    And validation result indicates acceptance
