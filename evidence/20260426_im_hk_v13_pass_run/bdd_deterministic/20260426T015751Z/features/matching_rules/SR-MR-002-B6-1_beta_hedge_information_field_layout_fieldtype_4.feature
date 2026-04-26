Feature: Beta Hedge Information Field Layout (FieldType 4)
  SR-MR-002-B6-1
  # paragraph_ids: MR-002-B6-1
  Beta Hedge Information Field Layout (FieldType 4)

  @positive @priority_high  # TC-SR-MR-002-B6-1-positive-01
  Scenario: Valid FieldType 4 record with all required columns
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And A FieldType 4 record (Beta hedge information for liquidation risk add-on) is present
    When The record is parsed with valid values for Bucket rate, Instrument beta, Delta equivalent position market value threshold, and Cash delta per quantity
    Then All four columns are successfully extracted
    And The record is accepted for margin calculation processing

  @boundary @priority_high  # TC-SR-MR-002-B6-1-boundary-01
  Scenario: FieldType 4 columns at maximum decimal and integer precision
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And A FieldType 4 record is present with values at maximum precision
    When Bucket rate and Instrument beta values have exactly 10 decimal places
    And Delta equivalent position market value threshold is at maximum INTEGER(X,0) value
    And Cash delta per quantity has exactly 10 decimal places
    Then All boundary values are accepted without truncation or rounding errors
    And The record is processed successfully

  @data_validation @priority_high  # TC-SR-MR-002-B6-1-data_validation-01
  Scenario: FieldType 4 column data type validation
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And A FieldType 4 record is being validated
    When Column values are checked against their expected data types
    And Bucket rate is validated as DECIMALS(X,10)
    And Instrument beta is validated as DECIMALS(X,10)
    And Delta equivalent position market value threshold is validated as INTEGER(X,0)
    And Cash delta per quantity is validated as DECIMALS(X,10)
    Then Each column passes its respective data type validation
    And Invalid data types are flagged with appropriate error messages
