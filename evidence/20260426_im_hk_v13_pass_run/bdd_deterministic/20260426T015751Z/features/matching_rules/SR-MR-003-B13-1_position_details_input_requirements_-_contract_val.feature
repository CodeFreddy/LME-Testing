Feature: Position Details Input Requirements - Contract Value and Market Value
  SR-MR-003-B13-1
  # paragraph_ids: MR-003-B13-1
  Position Details Input Requirements - Contract Value and Market Value

  @positive @priority_high  # TC-SR-MR-003-B13-1-positive-01
  Scenario: Calculate margin with valid Contract value and Market value in HKD equivalent
    Given Position details include valid Contract value in HKD equivalent
    And Position details include valid Market value in HKD equivalent
    When The system calculates total MTM and margin requirement using the position values
    Then The calculation completes successfully
    And Contract value and Market value are correctly incorporated into MTM and margin calculations

  @boundary @priority_high  # TC-SR-MR-003-B13-1-boundary-01
  Scenario: Calculate margin with large contract value
    Given Position details include a large Contract value (e.g., $384,000,000 as referenced in evidence)
    And Contract value is converted to HKD equivalent
    When The system calculates total MTM and margin requirement
    Then The calculation completes without overflow or precision errors
    And The large contract value is correctly factored into the receivable calculation

  @data_validation @priority_high  # TC-SR-MR-003-B13-1-data_validation-01
  Scenario: Validate Contract value and Market value HKD equivalent format
    Given Position data is retrieved from Marginable Position Report (RMAMP01)
    When The system validates Contract value and Market value fields for each position
    Then Contract value is present and expressed in HKD equivalent
    And Market value is present and expressed in HKD equivalent
    And Non-HKD values are flagged for currency conversion validation
