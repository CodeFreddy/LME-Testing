Feature: Total MTM and Margin Requirement Calculation Process
  SR-MR-003-B1-1
  # paragraph_ids: MR-003-B1-1
  Total MTM and Margin Requirement Calculation Process

  @positive @priority_high  # TC-SR-MR-003-B1-1-positive-01
  Scenario: Calculate Total MTM and Margin Requirement with Complete Inputs
    Given Risk Parameters and Margin Adjustments are available
    And Positions data is available
    And All market risk component inputs are accessible
    When The calculation process for Total MTM and Margin Requirement is executed
    Then Market Risk Components are calculated including HVaR, SVaR, and Portfolio Margin Floor
    And Flat Rate Margin and Liquidation Risk Add-on are computed
    And Market Risk Components are aggregated with Margin Adjustments
    And Total MTM and Margin Requirement values are produced

  @boundary @priority_high  # TC-SR-MR-003-B1-1-boundary-01
  Scenario: Boundary Condition for Portfolio with Zero Positions
    Given Risk Parameters and Margin Adjustments are available
    And Portfolio contains zero positions or minimal position count
    When The calculation process for Total MTM and Margin Requirement is executed
    Then The calculation completes without error
    And Resulting margin values reflect the boundary condition appropriately

  @data_validation @priority_high  # TC-SR-MR-003-B1-1-data_validation-01
  Scenario: Validation of Required Inputs for MTM and Margin Calculation
    Given A calculation request for Total MTM and Margin Requirement is initiated
    When The system validates presence and format of Risk Parameters, Margin Adjustments, and Positions data
    Then Each required input is validated for completeness
    And Data format and type compliance is confirmed
    And Validation errors are reported if any input is missing or malformed
