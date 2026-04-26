Feature: Total MTM and Margin Requirement Calculation Inputs
  SR-MR-003-B5-1
  # paragraph_ids: MR-003-B5-1
  Total MTM and Margin Requirement Calculation Inputs

  @positive @priority_high  # TC-SR-MR-003-B5-1-positive-01
  Scenario: Calculate total MTM and margin requirement with all required inputs
    Given Risk parameters including market risk and other risk components are available
    And Margin adjustments are configured
    And Position details include InstrumentID, Quantity, Contract value in HKD equivalent, and Market value in HKD equivalent
    When The calculation of total MTM and margin requirement is executed
    Then Total MTM and margin requirement is derived successfully
    And All risk parameters and margin adjustments are applied to the calculation

  @boundary @priority_high  # TC-SR-MR-003-B5-1-boundary-01
  Scenario: Calculate margin requirement with zero quantity position
    Given Risk parameters and margin adjustments are available
    And Position details include valid InstrumentID
    And Quantity is set to zero
    When The calculation of total MTM and margin requirement is executed
    Then Calculation completes without error
    And Result reflects zero position contribution to margin requirement

  @data_validation @priority_high  # TC-SR-MR-003-B5-1-data_validation-01
  Scenario: Validate required position detail fields are present
    Given Risk parameters and margin adjustments are available
    And Position data is being retrieved from Marginable Position Report
    When Position details are validated for required fields: InstrumentID, Quantity, Contract value, Market value
    Then Validation confirms InstrumentID is present
    And Validation confirms Quantity is present
    And Validation confirms Contract value in HKD equivalent is present
    And Validation confirms Market value in HKD equivalent is present
