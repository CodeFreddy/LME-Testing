Feature: IMRPF FieldType 3 Flat Rate Scenario Processing
  SR-MR-002-B19-1
  # paragraph_ids: MR-002-B19-1
  IMRPF FieldType 3 Flat Rate Scenario Processing

  @positive @priority_high  # TC-SR-MR-002-B19-1-positive-01
  Scenario: Process valid FieldType 3 flat rate records
    Given IMRPF file is received with valid header parameters
    And FieldType 3 records exist for instruments with flat rate return values
    When The system processes the FieldType 3 flat rate records
    Then Return for each instrument in flat rate margin component is extracted successfully
    And Flat rate values are available for margin calculation

  @boundary @priority_high  # TC-SR-MR-002-B19-1-boundary-01
  Scenario: Validate flat rate return value at specified decimal precision
    Given IMRPF file contains FieldType 3 records
    And Flat rate return value for instrument 658 is 0.12 and for instrument 3456 is 0.3
    When The system processes flat rate return values at maximum decimal precision
    Then Values with up to 10 decimal places are accepted
    And Values exceeding decimal precision are handled per specification

  @data_validation @priority_high  # TC-SR-MR-002-B19-1-data_validation-01
  Scenario: Validate FieldType 3 return value format
    Given IMRPF file contains FieldType 3 records for multiple instruments
    And Flat rate return values are provided in each record
    When The system validates the format of flat rate return values in FieldType 3 columns
    Then Each flat rate return value is validated as DECIMALS(X,10) format
    And Non-numeric or out-of-range values are rejected with appropriate error message
