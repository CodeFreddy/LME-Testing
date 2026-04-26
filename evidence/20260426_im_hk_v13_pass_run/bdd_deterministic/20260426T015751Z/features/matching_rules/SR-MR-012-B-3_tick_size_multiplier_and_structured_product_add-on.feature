Feature: Tick Size Multiplier and Structured Product Add-on Calculation
  SR-MR-012-B-3
  # paragraph_ids: MR-012-B-3
  Tick Size Multiplier and Structured Product Add-on Calculation

  @positive @priority_high  # TC-SR-MR-012-B-3-positive-01
  Scenario: Tick size multiplier calculated as 10 times FieldType 6 Column 2 value
    Given An instrument with FieldType 6 Column 2 value of 0.5 in the IMRPF
    When The tick size multiplier is calculated for the instrument
    Then The tick size multiplier equals 5 (10 x 0.5)

  @boundary @priority_high  # TC-SR-MR-012-B-3-boundary-01
  Scenario: Minimum tick size boundary at 0.001
    Given An instrument requiring tick size calculation
    When The tick size is set to the minimum value of 0.001
    Then The tick size is accepted as the minimum valid boundary

  @data_validation @priority_high  # TC-SR-MR-012-B-3-data_validation-01
  Scenario: Negative quantity excluded from structured product add-on calculation
    Given A portfolio containing InstrumentID 26883 with a negative quantity
    When The structured product add-on is calculated
    Then InstrumentID 26883 is excluded from the structured product add-on calculation
