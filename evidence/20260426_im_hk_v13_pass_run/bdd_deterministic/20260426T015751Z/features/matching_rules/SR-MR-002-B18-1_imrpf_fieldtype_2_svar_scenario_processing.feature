Feature: IMRPF FieldType 2 SVaR Scenario Processing
  SR-MR-002-B18-1
  # paragraph_ids: MR-002-B18-1
  IMRPF FieldType 2 SVaR Scenario Processing

  @positive @priority_high  # TC-SR-MR-002-B18-1-positive-01
  Scenario: Process valid FieldType 2 SVaR scenario records
    Given IMRPF file is received with header containing SVaR_Scen_Count=1018
    And FieldType 2 records exist for instruments with SVaR scenario return values
    When The system processes the FieldType 2 SVaR scenario records
    Then Scenario returns for each instrument in SVaR component are extracted successfully
    And Total number of scenarios matches SVaR_Scen_Count value of 1018

  @boundary @priority_high  # TC-SR-MR-002-B18-1-boundary-01
  Scenario: Validate SVaR scenario count boundary at exactly 1018
    Given IMRPF header specifies SVaR_Scen_Count=1018
    And FieldType 2 records contain exactly 1018 scenario return columns per instrument
    When The system validates the scenario count against SVaR_Scen_Count
    Then Validation passes when scenario count equals 1018
    And Processing proceeds without count mismatch error

  @data_validation @priority_high  # TC-SR-MR-002-B18-1-data_validation-01
  Scenario: Validate FieldType 2 scenario return decimal format
    Given IMRPF file contains FieldType 2 records for instrument ID 700
    And SVaR scenario return values are provided in the record
    When The system validates the format of scenario return values in FieldType 2 columns
    Then Each scenario return value is validated as DECIMALS(X,10) format
    And Invalid format values are rejected with appropriate error message
