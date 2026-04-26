Feature: Risk Parameters and Margin Adjustments Input Requirements
  SR-MR-003-B11-1
  # paragraph_ids: MR-003-B11-1
  Risk Parameters and Margin Adjustments Input Requirements

  @positive @priority_high  # TC-SR-MR-003-B11-1-positive-01
  Scenario: Calculate total MTM and margin requirement with all required risk parameters
    Given Risk parameters including market risk and other risk components are available
    And Margin adjustments including rounding on aggregated market-risk-component margin are available
    And Portfolio margin, flat rate margin, liquidation risk add-on, structured product add-on, corporate action position margin, and holiday add-on values are provided
    When The system calculates total MTM and margin requirement using the provided risk parameters and margin adjustments
    Then The calculation completes successfully
    And Total MTM and margin requirement values are derived and available

  @boundary @priority_high  # TC-SR-MR-003-B11-1-boundary-01
  Scenario: Calculate margin with minimum non-zero risk parameter values
    Given Risk parameters are set to minimum non-zero values
    And All margin adjustment components are set to minimum valid values
    When The system calculates total MTM and margin requirement
    Then The calculation completes without error
    And Resulting margin requirement reflects the minimum input values

  @data_validation @priority_high  # TC-SR-MR-003-B11-1-data_validation-01
  Scenario: Validate presence of all required risk parameters before calculation
    Given A margin calculation request is initiated
    When The system validates that all required risk parameters and margin adjustments are present
    Then Each required component is verified: Portfolio margin, Flat rate margin, Liquidation risk add-on, Structured product add-on, Corporate action position margin, Holiday add-on
    And Rounding on aggregated market-risk-component margin is verified
    And Consideration on favorable MTM and Application of margin credit are verified
