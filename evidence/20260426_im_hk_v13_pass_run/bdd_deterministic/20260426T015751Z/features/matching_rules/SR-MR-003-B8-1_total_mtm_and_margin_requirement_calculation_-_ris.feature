Feature: Total MTM and Margin Requirement Calculation - Risk Parameters
  SR-MR-003-B8-1
  # paragraph_ids: MR-003-B8-1
  Total MTM and Margin Requirement Calculation - Risk Parameters

  @positive @priority_high  # TC-SR-MR-003-B8-1-positive-01
  Scenario: Calculate total MTM and margin requirement with all required risk parameters
    Given Risk parameters including market risk and other risk components are available
    And Margin adjustments are provided from IMRPF and MTM/Margin Requirement Report sources
    When The system calculates total MTM and margin requirement using the provided risk parameters and margin adjustments
    Then Total MTM and margin requirement is successfully calculated
    And Calculation result is available for dissemination

  @boundary @priority_high  # TC-SR-MR-003-B8-1-boundary-01
  Scenario: Calculate margin requirement with minimum position quantity
    Given A portfolio contains a position with minimum quantity of 1 share
    And All required risk parameters are available
    When The system calculates total MTM and margin requirement for the minimum quantity position
    Then Calculation completes successfully for the minimum quantity
    And Margin requirement is computed proportionally

  @data_validation @priority_high  # TC-SR-MR-003-B8-1-data_validation-01
  Scenario: Validate presence of all required risk parameter components
    Given A margin calculation request is initiated
    When The system validates the presence of required risk parameters including market risk component, portfolio margin, flat rate margin, liquidation risk add-on, structured product add-on, corporate action position margin, and holiday add-on
    Then Validation confirms all required risk parameters are present
    And Calculation proceeds only after successful validation
