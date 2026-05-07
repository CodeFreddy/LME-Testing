Feature: Favorable MTM Calculation
  SR-IMHK-3_2_5_2-01
  # paragraph_ids: IMHK-3_2_5_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_2-01-positive-01
  Scenario: Calculate favorable MTM using portfolio values
    Given A clearing participant has a portfolio with Market valuePortfolio of -287,850,000 HKD
    And The portfolio has Contract valuePortfolio of -300,550,000 HKD
    When The system calculates favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio
    Then The favorable MTM is calculated as (-287,850,000) - (-300,550,000) = 12,700,000
    And A positive result indicates favorable MTM

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_2-01-boundary-01
  Scenario: Boundary between favorable MTM and MTM requirement
    Given A clearing participant has a portfolio where Market valuePortfolio equals Contract valuePortfolio
    When The system calculates favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio
    And The result equals zero
    Then The favorable MTM is zero
    And The MTM requirement is zero
    And Net margin equals the rounded aggregated market-risk-component margin

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_2-01-data_validation-01
  Scenario: Validate MTM requirement classification for negative result
    Given A clearing participant has a portfolio with Market valuePortfolio of -300,550,000 HKD
    And The portfolio has Contract valuePortfolio of -287,850,000 HKD
    When The system calculates favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio
    And The result is -12,700,000 (negative)
    Then The negative result is classified as MTM requirement
    And Favorable MTM is set to zero
    And The absolute value of MTM requirement (12,700,000) will be added after applying margin credit
