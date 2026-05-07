Feature: Rounding on Aggregated Market-risk-component Margin
  SR-IMHK-3_2_5_1-01
  # paragraph_ids: IMHK-3_2_5_1-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_1-01-positive-01
  Scenario: Aggregated margin rounding with standard rounding parameter
    Given Portfolio margin is 10,000,000
    And Flat rate margin is 15,180,000
    And Liquidation risk add-on is 266,865
    And Structured product add-on is 550,000
    And Corporate action position margin is 2,500,000
    And Holiday add-on is 18,433,039
    And Rounding parameter from Initial Margin Risk Parameter File is 10,000
    When Aggregated market-risk-component margin is calculated and rounded
    Then Aggregated margin before rounding equals 46,929,904
    And Rounded aggregated market-risk-component margin equals 46,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_1-01-boundary-01
  Scenario: Aggregated margin at exact rounding threshold
    Given Aggregated market-risk-component margin before rounding is 46,930,000
    And Rounding parameter from Initial Margin Risk Parameter File is 10,000
    When Rounding is applied to the aggregated margin
    Then Rounded aggregated market-risk-component margin equals 46,930,000
    And No upward adjustment is required as value is already at rounding threshold

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_1-01-data_validation-01
  Scenario: Aggregated margin calculation validates all required components
    Given Market risk component data is submitted for aggregated margin calculation
    When Aggregated market-risk-component margin calculation is performed
    Then Portfolio margin value is present and valid
    And Flat rate margin value is present and valid
    And Liquidation risk add-on value is present and valid
    And Structured product add-on value is present and valid
    And Corporate action position margin value is present and valid
    And Holiday add-on value is present and valid
    And Rounding parameter from Initial Margin Risk Parameter File is present and valid
