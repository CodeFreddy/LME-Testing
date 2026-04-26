Feature: Position Details for MTM and Margin Calculation
  SR-MR-003-B14-1
  # paragraph_ids: MR-003-B14-1
  Position Details for MTM and Margin Calculation

  @positive @priority_high  # TC-SR-MR-003-B14-1-positive-01
  Scenario: Calculate Total MTM and Margin Requirement with Complete Position Details
    Given A portfolio with valid position details including InstrumentID (e.g., 700 for Tencent Holdings)
    And Quantity (e.g., 1,000,000 shares)
    And Contract value in HKD equivalent
    And Market value in HKD equivalent
    When The system retrieves position information from the Marginable Position Report (RMAMP01)
    And The system calculates total MTM and margin requirement
    Then The calculation produces valid total MTM value
    And The calculation produces valid margin requirement value

  @boundary @priority_high  # TC-SR-MR-003-B14-1-boundary-01
  Scenario: Position Quantity Boundary Value Processing
    Given A portfolio position with quantity at boundary value (e.g., 1,000,000 shares)
    And Position details include InstrumentID, Contract value, and Market value
    When The system processes the position for marginable position report generation
    And The position snapshot is captured after margin call and day-end margin estimation
    Then The position is correctly included in the Marginable Position Report
    And Contract value and Market value are correctly calculated in HKD equivalent

  @data_validation @priority_high  # TC-SR-MR-003-B14-1-data_validation-01
  Scenario: Validate Required Position Detail Fields
    Given Position data submitted for margin calculation
    And Position data includes InstrumentID, Quantity, Contract value, and Market value fields
    When The system validates position details against required fields
    And The system checks data format and HKD equivalent conversion
    Then InstrumentID is present and valid
    And Quantity is present with correct sign (positive for long, negative for short)
    And Contract value is present in HKD equivalent
    And Market value is present in HKD equivalent
