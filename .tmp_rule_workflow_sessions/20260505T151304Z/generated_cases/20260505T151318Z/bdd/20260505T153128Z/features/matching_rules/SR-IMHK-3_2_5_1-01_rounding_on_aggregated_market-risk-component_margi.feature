Feature: Rounding on Aggregated Market-risk-component Margin
  SR-IMHK-3_2_5_1-01
  # paragraph_ids: IMHK-3_2_5_1-01
  Validates the two-step calculation and rounding of aggregated market-risk-component margin per the LME formula and rounding parameter from the Initial Margin Risk Parameter File.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_1-01-positive-01
  Scenario: Calculate and round aggregated market-risk-component margin
    Given A clearing participant has market risk components with Portfolio margin = 10,000,000
    And Flat rate margin = 15,180,000
    And Liquidation risk add-on = 266,865
    And Structured product add-on = 550,000
    And Corporate action position margin = 2,500,000
    And Holiday add-on = 18,433,039
    And The Initial Margin Risk Parameter File specifies a rounding parameter of 10,000
    When The system calculates the aggregated market-risk-component margin and applies rounding
    Then The aggregated margin is calculated as 46,929,904
    And The aggregated margin is rounded up to 46,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_1-01-boundary-01
  Scenario: Aggregated margin at exact rounding boundary
    Given A clearing participant has market risk components that sum to exactly 46,930,000
    And The Initial Margin Risk Parameter File specifies a rounding parameter of 10,000
    When The system rounds up the aggregated margin to the nearest 10,000
    Then The rounded aggregated market-risk-component margin remains 46,930,000

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_1-01-data_validation-01
  Scenario: Validate all market risk components included in aggregation formula
    Given A clearing participant has market risk components with values for Portfolio margin, Flat rate margin, Liquidation risk add-on, Structured product add-on, Corporate action position margin, and Holiday add-on
    And The Initial Margin Risk Parameter File contains a rounding parameter
    When The system calculates the aggregated market-risk-component margin
    Then All six components are summed in the correct formula order
    And The rounding parameter from the Initial Margin Risk Parameter File is retrieved and applied to round up the aggregated margin
