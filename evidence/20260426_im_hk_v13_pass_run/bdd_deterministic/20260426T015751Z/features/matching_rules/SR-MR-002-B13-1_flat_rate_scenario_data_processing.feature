Feature: Flat Rate Scenario Data Processing
  SR-MR-002-B13-1
  # paragraph_ids: MR-002-B13-1
  Flat Rate Scenario Data Processing

  @positive @priority_high  # TC-SR-MR-002-B13-1-positive-01
  Scenario: Process valid flat rate scenario data with correct field type
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains FieldType 3 records for Flat Rate Scenarios
    And Each instrument has a flat rate return value
    When The system processes the flat rate scenario data for each instrument
    And The return values are parsed from FieldType 3 columns
    Then The flat rate returns are successfully parsed
    And The processing result is not null
    And The flat rate data is available for margin component calculation

  @boundary @priority_high  # TC-SR-MR-002-B13-1-boundary-01
  Scenario: Process flat rate scenario data at decimal precision boundary
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And FieldType 3 records contain flat rate return values
    And Return values have exactly 10 decimal places (maximum supported)
    When The system processes flat rate return values at maximum decimal precision
    And Values are validated against DECIMALS(X,10) format
    Then Values with 10 decimal places are accepted and processed correctly
    And No precision loss occurs during processing

  @data_validation @priority_high  # TC-SR-MR-002-B13-1-data_validation-01
  Scenario: Validate flat rate return data format as DECIMALS(X,10)
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains FieldType 3 records with flat rate return values
    When The system validates the format of each flat rate return value
    And Each return value is checked against DECIMALS(X,10) format
    Then Values conforming to DECIMALS(X,10) format are accepted
    And Values exceeding maximum decimal places are rejected or flagged
