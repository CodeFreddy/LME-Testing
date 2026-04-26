Feature: Instrument Delta Information Field Layout (FieldType 5)
  SR-MR-002-B7-1
  # paragraph_ids: MR-002-B7-1
  Instrument Delta Information Field Layout (FieldType 5)

  @positive @priority_high  # TC-SR-MR-002-B7-1-positive-01
  Scenario: Valid FieldType 5 record with all required columns
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And A FieldType 5 record (Instrument delta information for liquidation risk add-on) is present
    When The record is parsed with valid values for Underlying group, Delta, Conversion ratio, and Cash delta per quantity
    Then All four columns are successfully extracted
    And The record is accepted for liquidation risk add-on calculation

  @boundary @priority_high  # TC-SR-MR-002-B7-1-boundary-01
  Scenario: FieldType 5 columns at maximum decimal precision
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And A FieldType 5 record is present with values at maximum precision
    When Delta value has exactly 10 decimal places
    And Conversion ratio has exactly 10 decimal places
    And Cash delta per quantity has exactly 10 decimal places
    Then All boundary values are accepted without truncation or rounding errors
    And The record is processed successfully

  @data_validation @priority_high  # TC-SR-MR-002-B7-1-data_validation-01
  Scenario: FieldType 5 column data type validation
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And A FieldType 5 record is being validated
    When Column values are checked against their expected data types
    And Underlying group is validated as TEXT
    And Delta is validated as DECIMALS(X,10)
    And Conversion ratio is validated as DECIMALS(X,10)
    And Cash delta per quantity is validated as DECIMALS(X,10)
    Then Each column passes its respective data type validation
    And Invalid data types are flagged with appropriate error messages
