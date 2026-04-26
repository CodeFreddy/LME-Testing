Feature: Marginable Position Report Data Retrieval
  SR-MR-003-B7-1
  # paragraph_ids: MR-003-B7-1
  Marginable Position Report Data Retrieval

  @positive @priority_high  # TC-SR-MR-003-B7-1-positive-01
  Scenario: Retrieve position data from Marginable Position Report for calculation
    Given Margin call or day-end margin estimation process has completed
    And Marginable Position Report (RMAMP01) is available
    When Position information is retrieved from Marginable Position Report for calculation
    Then InstrumentID for each position is retrieved
    And Quantity for each position is retrieved
    And Contract value in HKD equivalent is retrieved
    And Market value in HKD equivalent is retrieved

  @boundary @priority_high  # TC-SR-MR-003-B7-1-boundary-01
  Scenario: Calculate margin with equal contract value and market value
    Given Position data is retrieved from Marginable Position Report
    And Contract value in HKD equivalent equals Market value in HKD equivalent
    When The calculation of total MTM and margin requirement is executed
    Then Calculation completes successfully
    And MTM reflects zero unrealized gain or loss for the position

  @data_validation @priority_high  # TC-SR-MR-003-B7-1-data_validation-01
  Scenario: Validate InstrumentID format from position data
    Given Position data is retrieved from Marginable Position Report (RMAMP01)
    And InstrumentID field is present in the position data
    When InstrumentID is validated for correct identifier format
    Then InstrumentID is validated as a valid numeric or alphanumeric identifier
    And Invalid InstrumentID format triggers validation error
