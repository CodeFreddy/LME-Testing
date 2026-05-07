Feature: Rounding on Aggregated Market-risk-component Margin
  SR-IMHK-3_2_5_1-01
  # paragraph_ids: IMHK-3_2_5_1-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_1-01-positive-01
  Scenario: Calculate and round aggregated market-risk-component margin
    Given Portfolio margin is 10,000,000
    And Flat rate margin is 15,180,000
    And Liquidation risk add-on is 266,865
    And Structured product add-on is 550,000
    And Corporate action position margin is 2,500,000
    And Holiday add-on is 18,433,039
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When Aggregated market-risk-component margin is calculated
    And Result is rounded up to nearest 10,000
    Then Aggregated market-risk-component margin equals 46,929,904
    And Rounded aggregated market-risk-component margin equals 46,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_1-01-boundary-01
  Scenario: Rounding when aggregated margin is exact multiple of rounding parameter
    Given Aggregated market-risk-component margin is exactly 46,930,000
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When The system applies rounding to the aggregated margin
    Then Rounded aggregated market-risk-component margin remains 46,930,000
    And No upward adjustment is needed as value is already at rounding boundary

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_1-01-data_validation-01
  Scenario: Validate all market risk components are present for aggregation
    Given A clearing participant has margin calculation request
    When The system validates input data for aggregated margin calculation
    Then Portfolio margin value is present
    And Flat rate margin value is present
    And Liquidation risk add-on value is present
    And Structured product add-on value is present
    And Corporate action position margin value is present
    And Holiday add-on value is present
    And Rounding parameter from Initial Margin Risk Parameter File is retrieved
