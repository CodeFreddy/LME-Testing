Feature: Total MTM and Margin Requirement Calculation - Currency Values
  SR-MR-003-B10-1
  # paragraph_ids: MR-003-B10-1
  Total MTM and Margin Requirement Calculation - Currency Values

  @positive @priority_high  # TC-SR-MR-003-B10-1-positive-01
  Scenario: Calculate total MTM with Contract value and Market value in HKD equivalent
    Given Position includes Contract value and Market value converted to HKD equivalent
    And All other required position details are available
    When The system calculates total MTM and margin requirement using HKD-equivalent values
    Then Total MTM is calculated correctly in HKD
    And Margin requirement is derived from HKD-denominated values

  @boundary @priority_high  # TC-SR-MR-003-B10-1-boundary-01
  Scenario: Calculate margin requirement with large contract value
    Given A position has contract value of $384,000,000 HKD equivalent
    And All required position details are provided
    When The system calculates total MTM and margin requirement for the large contract value position
    Then Calculation completes successfully for the large contract value
    And CP receivable amount is correctly reflected in the calculation

  @data_validation @priority_high  # TC-SR-MR-003-B10-1-data_validation-01
  Scenario: Validate Contract value and Market value are in HKD equivalent
    Given Position data includes Contract value and Market value fields
    When The system validates that Contract value and Market value are expressed in HKD equivalent
    Then Validation confirms monetary values are in HKD equivalent format
    And Non-HKD values trigger conversion requirement or validation error
