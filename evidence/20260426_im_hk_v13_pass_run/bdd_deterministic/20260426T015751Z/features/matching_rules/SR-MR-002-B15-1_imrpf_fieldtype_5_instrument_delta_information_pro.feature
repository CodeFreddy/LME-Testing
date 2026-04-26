Feature: IMRPF FieldType 5 Instrument Delta Information Processing
  SR-MR-002-B15-1
  # paragraph_ids: MR-002-B15-1
  IMRPF FieldType 5 Instrument Delta Information Processing

  @positive @priority_high  # TC-SR-MR-002-B15-1-positive-01
  Scenario: Valid FieldType 5 Instrument Delta Record Processing
    Given The IMRPF file is being processed
    And A record with FieldType 5 exists for an instrument
    When The system processes the FieldType 5 record containing underlying group, delta, conversion ratio, and cash delta per quantity
    Then The instrument delta information is included in the liquidation risk add-on calculation
    And All four columns are parsed and stored correctly

  @boundary @priority_high  # TC-SR-MR-002-B15-1-boundary-01
  Scenario: FieldType 5 Conversion Ratio Boundary Values
    Given The IMRPF file is being processed
    And A FieldType 5 record contains conversion ratio values
    When The system processes FieldType 5 records with conversion ratio values of 100 (as shown in sample data)
    Then The conversion ratio is accepted and applied correctly in delta calculations
    And No precision loss occurs for the conversion ratio value

  @data_validation @priority_high  # TC-SR-MR-002-B15-1-data_validation-01
  Scenario: FieldType 5 Underlying Group Text Format Validation
    Given The IMRPF file is being processed
    And A FieldType 5 record contains an underlying group identifier
    When The system validates the underlying group field which contains stock codes or identifiers (e.g., 700, 1299)
    Then The TEXT format is validated and accepted
    And The underlying group is correctly associated with the instrument for delta calculation
