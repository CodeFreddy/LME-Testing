Feature: IMRPF FieldType 1 HVaR Scenario Processing
  SR-MR-002-B17-1
  # paragraph_ids: MR-002-B17-1
  IMRPF FieldType 1 HVaR Scenario Processing

  @positive @priority_high  # TC-SR-MR-002-B17-1-positive-01
  Scenario: Process valid FieldType 1 HVaR scenario records
    Given IMRPF file is received with header containing Valuation_DT, HVaR_WGT=0.75, SVaR_WGT=0.25, HVaR_Scen_Count=1000
    And FieldType 1 records exist for instruments with scenario return values
    When The system processes the FieldType 1 HVaR scenario records
    Then Scenario returns for each instrument in HVaR component are extracted successfully
    And Total number of scenarios matches HVaR_Scen_Count value of 1000

  @boundary @priority_high  # TC-SR-MR-002-B17-1-boundary-01
  Scenario: Validate HVaR scenario count boundary at exactly 1000
    Given IMRPF header specifies HVaR_Scen_Count=1000
    And FieldType 1 records contain exactly 1000 scenario return columns per instrument
    When The system validates the scenario count against HVaR_Scen_Count
    Then Validation passes when scenario count equals 1000
    And Processing proceeds without count mismatch error

  @data_validation @priority_high  # TC-SR-MR-002-B17-1-data_validation-01
  Scenario: Validate FieldType 1 scenario return decimal format
    Given IMRPF file contains FieldType 1 records for instrument ID 700
    And Scenario return values are provided in the record
    When The system validates the format of scenario return values in FieldType 1 columns
    Then Each scenario return value is validated as DECIMALS(X,10) format
    And Invalid format values are rejected with appropriate error message
