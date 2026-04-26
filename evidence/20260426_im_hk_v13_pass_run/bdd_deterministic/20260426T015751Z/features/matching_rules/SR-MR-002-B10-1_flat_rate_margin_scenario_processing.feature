Feature: Flat Rate Margin Scenario Processing
  SR-MR-002-B10-1
  # paragraph_ids: MR-002-B10-1
  Flat Rate Margin Scenario Processing

  @positive @priority_high  # TC-SR-MR-002-B10-1-positive-01
  Scenario: Process valid Flat Rate scenario records for instruments
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And The file contains FieldType 3 records for Flat Rate Scenarios
    When The system processes the FieldType 3 records with return values such as 0.12 for instrument 658 and 0.3 for instrument 3456
    Then The Flat Rate scenario returns are successfully parsed
    And The return values are available for flat rate margin calculation
    And The processing result is available for margin calculation

  @boundary @priority_high  # TC-SR-MR-002-B10-1-boundary-01
  Scenario: Validate Flat Rate return value at boundary precision
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And FieldType 3 records contain return values for flat rate margin component
    When The system processes Flat Rate return values with up to 10 decimal places precision
    Then Return values with maximum 10 decimal places are accepted
    And The precision is maintained for flat rate margin calculation
    And No precision loss occurs during processing

  @data_validation @priority_high  # TC-SR-MR-002-B10-1-data_validation-01
  Scenario: Validate Flat Rate scenario data format and instrument identification
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And FieldType 3 records contain InstrumentID and return values
    When The system validates InstrumentID (e.g., 658, 3456, 3457, 3606) and corresponding return values (e.g., 0.12, 0.3)
    Then InstrumentID is validated as TEXT format (stock code or underlying stock code)
    And Return values are validated against DECIMALS(X,10) format
    And Invalid InstrumentID or return values are rejected with appropriate error message
