Feature: Position Details Input Requirements - InstrumentID and Quantity
  SR-MR-003-B12-1
  # paragraph_ids: MR-003-B12-1
  Position Details Input Requirements - InstrumentID and Quantity

  @positive @priority_high  # TC-SR-MR-003-B12-1-positive-01
  Scenario: Calculate margin with valid InstrumentID and Quantity
    Given Position details include valid InstrumentID (e.g., 700 for Tencent Holdings)
    And Position details include valid Quantity (e.g., 1,000,000 shares)
    When The system calculates total MTM and margin requirement using the position details
    Then The calculation completes successfully
    And Position details are correctly incorporated into the margin calculation

  @boundary @priority_high  # TC-SR-MR-003-B12-1-boundary-01
  Scenario: Calculate margin with maximum quantity value
    Given Position details include a valid InstrumentID
    And Quantity is set to a large value (e.g., 1,000,000 shares as referenced in evidence)
    When The system calculates total MTM and margin requirement
    Then The calculation completes without overflow or precision errors
    And The large quantity is correctly factored into the margin requirement

  @data_validation @priority_high  # TC-SR-MR-003-B12-1-data_validation-01
  Scenario: Validate InstrumentID and Quantity data format
    Given Position data is retrieved from Marginable Position Report (RMAMP01)
    When The system validates InstrumentID and Quantity fields for each position
    Then InstrumentID is present and in valid format
    And Quantity is present and represents a valid numeric share quantity
    And Invalid or missing fields are flagged as data validation errors
