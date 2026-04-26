Feature: IMRPF FieldType 4 Beta Hedge Information Processing
  SR-MR-002-B14-1
  # paragraph_ids: MR-002-B14-1
  IMRPF FieldType 4 Beta Hedge Information Processing

  @positive @priority_high  # TC-SR-MR-002-B14-1-positive-01
  Scenario: Valid FieldType 4 Beta Hedge Record Processing
    Given The IMRPF file is being processed
    And A record with FieldType 4 exists for an instrument
    When The system processes the FieldType 4 record containing bucket rate, instrument beta, delta equivalent position market value threshold, and cash delta per quantity
    Then The beta hedge information is included in the liquidation risk add-on calculation
    And All four columns are parsed and stored correctly

  @boundary @priority_high  # TC-SR-MR-002-B14-1-boundary-01
  Scenario: FieldType 4 Maximum Delta Threshold Boundary
    Given The IMRPF file is being processed
    And A FieldType 4 record contains a delta equivalent position market value threshold at the maximum supported integer value
    When The system processes the FieldType 4 record with threshold value 300000000
    Then The threshold value is accepted and stored without overflow
    And The beta hedge calculation proceeds correctly

  @data_validation @priority_high  # TC-SR-MR-002-B14-1-data_validation-01
  Scenario: FieldType 4 Decimal Precision Validation
    Given The IMRPF file is being processed
    And A FieldType 4 record contains bucket rate and instrument beta values
    When The system validates the decimal precision of bucket rate (e.g., 0.0022) and instrument beta (e.g., 0.9, 1.1, 1.2, 1.3)
    Then Values are validated against DECIMALS(X,10) format specification
    And Values exceeding 10 decimal places are rejected or truncated per system rules
