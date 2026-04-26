Feature: IMRPF FieldType 6 Price Threshold and Structured Product Add-On Processing
  SR-MR-002-B16-1
  # paragraph_ids: MR-002-B16-1
  IMRPF FieldType 6 Price Threshold and Structured Product Add-On Processing

  @positive @priority_high  # TC-SR-MR-002-B16-1-positive-01
  Scenario: Valid FieldType 6 Price Threshold Record Processing
    Given The IMRPF file is being processed
    And A record with FieldType 6 exists for an instrument
    When The system processes the FieldType 6 record containing price threshold and one-tenth of tick size multiplier
    Then The price threshold and add-on information is included in the structured product add-on calculation
    And Both columns are parsed and stored correctly

  @boundary @priority_high  # TC-SR-MR-002-B16-1-boundary-01
  Scenario: FieldType 6 Tick Size Multiplier Boundary Values
    Given The IMRPF file is being processed
    And A FieldType 6 record contains one-tenth of tick size multiplier values
    When The system processes FieldType 6 records with tick size multiplier value of 0.5 (as shown in sample data)
    Then The tick size multiplier is accepted and applied correctly in structured product add-on calculations
    And The one-tenth scaling is correctly interpreted

  @data_validation @priority_high  # TC-SR-MR-002-B16-1-data_validation-01
  Scenario: FieldType 6 Price Threshold Decimal Format Validation
    Given The IMRPF file is being processed
    And A FieldType 6 record contains price threshold values
    When The system validates the decimal precision of price threshold values (e.g., 0.02)
    Then Values are validated against DECIMALS(X,10) format specification
    And Values exceeding 10 decimal places are rejected or truncated per system rules
