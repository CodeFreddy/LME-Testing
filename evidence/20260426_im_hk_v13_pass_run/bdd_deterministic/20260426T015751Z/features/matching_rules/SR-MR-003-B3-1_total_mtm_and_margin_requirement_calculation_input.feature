Feature: Total MTM and Margin Requirement Calculation Inputs
  SR-MR-003-B3-1
  # paragraph_ids: MR-003-B3-1
  Total MTM and Margin Requirement Calculation Inputs

  @positive @priority_high  # TC-SR-MR-003-B3-1-positive-01
  Scenario: Margin calculation proceeds with all required risk parameters from IMRPF
    Given IMRPF contains market risk components: Portfolio margin, Flat rate margin, Liquidation risk add-on, Structured product add-on, Corporate action position margin, Holiday add-on
    And IMRPF contains margin adjustments: Rounding on aggregated market-risk-component margin
    When The system calculates total MTM and margin requirement
    Then All market risk components from IMRPF are incorporated
    And Margin adjustments are applied
    And Calculated value is available

  @boundary @priority_high  # TC-SR-MR-003-B3-1-boundary-01
  Scenario: Margin calculation with minimum position quantity boundary
    Given A position with InstrumentID is provided
    And Quantity is set to minimum threshold value (e.g., 1 share)
    When The system calculates total MTM and margin requirement
    Then The calculation processes the minimum quantity position
    And Result reflects the minimum position margin requirement

  @data_validation @priority_high  # TC-SR-MR-003-B3-1-data_validation-01
  Scenario: Margin calculation rejected when required position field is missing
    Given Position data is received from Marginable Position Report (RMAMP01)
    And The InstrumentID field is missing or null
    When The system validates required position details for margin calculation
    Then Validation fails with error indicating missing InstrumentID
    And Margin calculation does not proceed
