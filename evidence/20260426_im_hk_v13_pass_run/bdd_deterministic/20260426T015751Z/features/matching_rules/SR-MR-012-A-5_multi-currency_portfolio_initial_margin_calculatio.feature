Feature: Multi-Currency Portfolio Initial Margin Calculation
  SR-MR-012-A-5
  # paragraph_ids: MR-012-A-5
  Multi-Currency Portfolio Initial Margin Calculation

  @positive @priority_high  # TC-SR-MR-012-A-5-positive-01
  Scenario: Calculate initial margin for multi-currency portfolio
    Given A portfolio containing positions in multiple currencies
    And The calculation logic from Appendix 4.6 is available
    When The initial margin calculation is performed for the multi-currency portfolio
    Then The calculated margin amount is returned
    And The calculation follows the logic specified in Appendix 4.6

  @boundary @priority_high  # TC-SR-MR-012-A-5-boundary-01
  Scenario: Minimum currency count for multi-currency calculation
    Given A portfolio containing positions in exactly two different currencies
    And The calculation logic from Appendix 4.6 is available
    When The initial margin calculation is performed
    Then The multi-currency calculation logic is invoked
    And A valid margin amount is calculated

  @data_validation @priority_high  # TC-SR-MR-012-A-5-data_validation-01
  Scenario: Validate currency data inputs for margin calculation
    Given A portfolio with positions in multiple currencies
    And Currency data fields are present for all positions
    When The initial margin calculation is initiated
    Then Currency codes are validated against supported currency list
    And Exchange rates for all currencies are available
    And Calculation proceeds only if all currency data is valid
