Feature: Favorable MTM Calculation
  SR-IMHK-3_2_5_2-01
  # paragraph_ids: IMHK-3_2_5_2-01
  Validates the calculation of Favorable MTM (or MTM requirement) using the formula: Market valuePortfolio - Contract valuePortfolio, ensuring correct handling of positive, negative, boundary, and validation conditions.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_2-01-positive-01
  Scenario: Calculate Favorable MTM using portfolio market and contract values
    Given A clearing participant has a portfolio with market value of -300,550,000 HKD
    And The portfolio has a contract value of -287,850,000 HKD
    When The system calculates Favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio
    Then The Favorable MTM (or MTM requirement) is calculated as -12,700,000 HKD
    And The negative result is identified as an MTM requirement
    And The favorable MTM is set to zero since the result is negative

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_2-01-boundary-01
  Scenario: Favorable MTM calculation at zero result boundary
    Given A clearing participant has a portfolio with market value of -250,000,000 HKD
    And The portfolio has a contract value of -250,000,000 HKD
    When The system calculates Favorable MTM using the formula: Market valuePortfolio - Contract valuePortfolio
    Then The Favorable MTM (or MTM requirement) is calculated as 0 HKD
    And The result at the boundary is validated as neither favorable MTM nor MTM requirement

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_2-01-data_validation-01
  Scenario: Validate required input fields for Favorable MTM calculation
    Given A clearing participant submits a portfolio for initial margin calculation
    And The portfolio is missing the Market valuePortfolio data field
    When The system attempts to calculate Favorable MTM
    Then The calculation is rejected with a validation error
    And An error message indicates that Market valuePortfolio is a required field for Favorable MTM calculation
