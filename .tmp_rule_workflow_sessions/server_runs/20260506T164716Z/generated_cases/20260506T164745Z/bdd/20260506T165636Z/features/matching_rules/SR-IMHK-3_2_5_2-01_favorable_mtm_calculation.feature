Feature: Favorable MTM Calculation
  SR-IMHK-3_2_5_2-01
  # paragraph_ids: IMHK-3_2_5_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_2-01-positive-01
  Scenario: Calculate favorable MTM using portfolio values
    Given A clearing participant portfolio with Market valuePortfolio of -300,550,000
    And Contract valuePortfolio of -287,850,000
    When The system calculates favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio
    Then Favorable MTM equals -12,700,000
    And The negative number refers to a MTM requirement
    And Favorable MTM is zero when result is negative

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_2-01-boundary-01
  Scenario: Calculate net margin when favorable MTM is zero
    Given Rounded aggregated market-risk-component margin of 46,930,000
    And Favorable MTM equals zero due to negative MTM requirement result
    When The system calculates net margin using: Maximum(0, Rounded aggregated market-risk-component margin – Favorable MTM)
    Then Net margin equals Maximum[0, (46,930,000 – 0)]
    And Net margin equals 46,930,000

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_2-01-data_validation-01
  Scenario: Validate mutual exclusivity of favorable MTM and MTM requirement
    Given A portfolio with calculated favorable MTM or MTM requirement
    When The system validates the calculation result for reporting
    Then Favorable MTM and MTM requirement are mutually exclusive
    And Only one of favorable MTM or MTM requirement has a non-zero value
    And Absolute value is shown in MTM and Margin Requirement Report
