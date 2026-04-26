Feature: Total MTM and Margin Requirement Calculation - Position Details
  SR-MR-003-B9-1
  # paragraph_ids: MR-003-B9-1
  Total MTM and Margin Requirement Calculation - Position Details

  @positive @priority_high  # TC-SR-MR-003-B9-1-positive-01
  Scenario: Calculate total MTM and margin requirement with complete position details
    Given Position details include valid InstrumentID, Quantity, Contract value, and Market value
    And Position data is retrieved from Marginable Position Report (RMAMP01)
    When The system calculates total MTM and margin requirement using the complete position details
    Then Total MTM and margin requirement is successfully calculated
    And Result is disseminated to CP after margin call and day-end margin estimation process

  @boundary @priority_high  # TC-SR-MR-003-B9-1-boundary-01
  Scenario: Calculate margin requirement with large quantity position
    Given A portfolio contains a position with quantity of 1,000,000 shares
    And All required position details are provided
    When The system calculates total MTM and margin requirement for the large quantity position
    Then Calculation completes successfully for the large quantity
    And Contract value and market value are correctly computed for the position

  @data_validation @priority_high  # TC-SR-MR-003-B9-1-data_validation-01
  Scenario: Validate InstrumentID format and presence
    Given Position data is submitted for margin calculation
    When The system validates that InstrumentID is present and matches expected format (e.g., numeric identifier like 700 for Tencent Holdings)
    Then Validation confirms InstrumentID is present and valid
    And Invalid or missing InstrumentID triggers validation error
