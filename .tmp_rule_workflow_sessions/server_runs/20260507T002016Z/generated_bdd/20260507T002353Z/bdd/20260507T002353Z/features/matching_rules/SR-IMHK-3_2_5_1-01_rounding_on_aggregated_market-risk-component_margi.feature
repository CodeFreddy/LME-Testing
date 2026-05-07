Feature: Rounding on Aggregated Market-risk-component Margin
  SR-IMHK-3_2_5_1-01
  # paragraph_ids: IMHK-3_2_5_1-01
  Validates the calculation, rounding, and component validation of aggregated market-risk-component margin per LME Rulebook requirements.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_1-01-positive-01
  Scenario: Calculate and round aggregated market-risk-component margin
    Given Portfolio margin is 10,000,000
    And Flat rate margin is 15,180,000
    And Liquidation risk add-on is 266,865
    And Structured product add-on is 550,000
    And Corporate action position margin is 2,500,000
    And Holiday add-on is 18,433,039
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When the clearing participant calculates the aggregated market-risk-component margin
    And the system applies rounding up to the nearest 10,000
    Then the aggregated margin before rounding is calculated as 46,929,904
    And the rounded aggregated market-risk-component margin is 46,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_1-01-boundary-01
  Scenario: Rounding when aggregated margin is exact multiple of rounding parameter
    Given Aggregated margin before rounding is exactly 46,930,000
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When the system applies rounding up to the nearest 10,000
    Then the rounded aggregated market-risk-component margin remains 46,930,000
    And no upward adjustment is applied since value is already at the rounding boundary

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_1-01-data_validation-01
  Scenario: Validate all margin components are present for aggregation calculation
    Given A clearing participant portfolio with margin calculation request
    When the system validates the presence of all margin components
    And the system validates the rounding parameter from the Initial Margin Risk Parameter File
    Then Portfolio margin is present and valid
    And Flat rate margin is present and valid
    And Liquidation risk add-on is present and valid
    And Structured product add-on is present and valid
    And Corporate action position margin is present and valid
    And Holiday add-on is present and valid
    And Rounding parameter is retrieved from the Initial Margin Risk Parameter File
