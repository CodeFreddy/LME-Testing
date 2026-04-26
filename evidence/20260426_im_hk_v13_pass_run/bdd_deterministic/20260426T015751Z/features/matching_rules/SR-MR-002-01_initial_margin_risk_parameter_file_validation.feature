Feature: Initial Margin Risk Parameter File Validation
  SR-MR-002-01
  # paragraph_ids: MR-002-01
  Initial Margin Risk Parameter File Validation

  @positive @priority_high  # TC-SR-MR-002-01-positive-01
  Scenario: Valid Initial Margin Risk Parameter File Layout and Specifications
    Given An Initial Margin Risk Parameter File is prepared for processing
    And The file conforms to the expected layout structure
    When The Initial Margin Risk Parameter File is submitted for validation
    Then The file is accepted
    And The layout and specifications are validated successfully

  @negative @priority_high  # TC-SR-MR-002-01-negative-01
  Scenario: Invalid Initial Margin Risk Parameter File Layout Rejection
    Given An Initial Margin Risk Parameter File is prepared for processing
    And The file does not conform to the expected layout structure
    When The Initial Margin Risk Parameter File is submitted for validation
    Then The file is rejected
    And A validation error is returned indicating layout or specification non-compliance

  @data_validation @priority_high  # TC-SR-MR-002-01-data_validation-01
  Scenario: Initial Margin Risk Parameter File Data Format Validation
    Given An Initial Margin Risk Parameter File is prepared for processing
    And The file layout structure is correct
    When Individual data fields within the file are validated against format specifications
    Then Each data field is validated for correct type, format, and allowable values
    And Validation results are reported for each field
