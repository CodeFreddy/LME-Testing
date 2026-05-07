Feature: Rounding on Aggregated Market-risk-component Margin
  SR-IMHK-3_2_5_1-01
  # paragraph_ids: IMHK-3_2_5_1-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_1-01-positive-01
  Scenario: Aggregated margin rounded up to nearest rounding parameter
    Given Portfolio margin is 10,000,000 HKD
    And Flat rate margin is 15,180,000 HKD
    And Liquidation risk add-on is 266,865 HKD
    And Structured product add-on is 550,000 HKD
    And Corporate action position margin is 2,500,000 HKD
    And Holiday add-on is 18,433,039 HKD
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When The aggregated market-risk-component margin is calculated and rounded up
    Then Aggregated margin before rounding equals 46,929,904 HKD
    And Rounded aggregated market-risk-component margin equals 46,930,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_1-01-boundary-01
  Scenario: Rounding when aggregated margin is exact multiple of rounding parameter
    Given Aggregated market-risk-component margin before rounding is exactly 50,000,000 HKD
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When The rounding up to nearest 10,000 is applied
    Then Rounded aggregated market-risk-component margin remains 50,000,000 HKD
    And No upward adjustment is needed as value is already at rounding boundary

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_1-01-data_validation-01
  Scenario: Aggregated margin calculation validates all component data
    Given A clearing participant has margin components to be aggregated
    When The system validates presence of Portfolio margin, Flat rate margin, Liquidation risk add-on, Structured product add-on, Corporate action position margin, and Holiday add-on
    And The system retrieves the rounding parameter from the Initial Margin Risk Parameter File
    Then All six margin components are validated as present with numeric values
    And Rounding parameter is retrieved successfully from Initial Margin Risk Parameter File
    And Rounding parameter is a positive integer value
