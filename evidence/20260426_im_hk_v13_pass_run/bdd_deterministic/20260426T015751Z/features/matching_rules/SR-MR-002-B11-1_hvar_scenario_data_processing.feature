Feature: HVaR Scenario Data Processing
  SR-MR-002-B11-1
  # paragraph_ids: MR-002-B11-1
  HVaR Scenario Data Processing

  @positive @priority_high  # TC-SR-MR-002-B11-1-positive-01
  Scenario: Process valid HVaR scenario data with correct field type and scenario count
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains FieldType 1 records for HVaR Scenarios
    And HVaR_Scen_Count is set to 1000
    When The system processes the HVaR scenario data for each instrument
    And The total number of scenario columns equals HVaR_Scen_Count (1000)
    Then The HVaR scenario returns are successfully parsed
    And The processing result is not null
    And The scenario data is available for HVaR component calculation

  @boundary @priority_high  # TC-SR-MR-002-B11-1-boundary-01
  Scenario: Process HVaR scenario data at exact HVaR_Scen_Count boundary of 1000
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And HVaR_Scen_Count is set to 1000
    And FieldType 1 records contain exactly 1000 scenario columns
    When The system validates the scenario count against HVaR_Scen_Count
    And The system processes the boundary condition of exactly 1000 scenarios
    Then The validation accepts the scenario count as matching HVaR_Scen_Count
    And All 1000 scenario returns are processed for HVaR calculation

  @data_validation @priority_high  # TC-SR-MR-002-B11-1-data_validation-01
  Scenario: Validate HVaR scenario return data format as DECIMALS(X,10)
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains FieldType 1 records with scenario return values
    When The system validates the format of each scenario return value
    And Each return value is checked against DECIMALS(X,10) format
    Then Values conforming to DECIMALS(X,10) format are accepted
    And Values exceeding maximum decimal places are rejected or flagged
