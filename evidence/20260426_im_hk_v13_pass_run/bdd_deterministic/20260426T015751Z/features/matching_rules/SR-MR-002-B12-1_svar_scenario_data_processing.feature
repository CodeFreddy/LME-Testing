Feature: SVaR Scenario Data Processing
  SR-MR-002-B12-1
  # paragraph_ids: MR-002-B12-1
  SVaR Scenario Data Processing

  @positive @priority_high  # TC-SR-MR-002-B12-1-positive-01
  Scenario: Process valid SVaR scenario data with correct field type and scenario count
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains FieldType 2 records for SVaR Scenarios
    And SVaR_Scen_Count is set to 1018
    When The system processes the SVaR scenario data for each instrument
    And The total number of scenario columns equals SVaR_Scen_Count (1018)
    Then The SVaR scenario returns are successfully parsed
    And The processing result is not null
    And The scenario data is available for SVaR component calculation

  @boundary @priority_high  # TC-SR-MR-002-B12-1-boundary-01
  Scenario: Process SVaR scenario data at exact SVaR_Scen_Count boundary of 1018
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And SVaR_Scen_Count is set to 1018
    And FieldType 2 records contain exactly 1018 scenario columns
    When The system validates the scenario count against SVaR_Scen_Count
    And The system processes the boundary condition of exactly 1018 scenarios
    Then The validation accepts the scenario count as matching SVaR_Scen_Count
    And All 1018 scenario returns are processed for SVaR calculation

  @data_validation @priority_high  # TC-SR-MR-002-B12-1-data_validation-01
  Scenario: Validate SVaR scenario return data format as DECIMALS(X,10)
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains FieldType 2 records with scenario return values
    When The system validates the format of each scenario return value
    And Each return value is checked against DECIMALS(X,10) format
    Then Values conforming to DECIMALS(X,10) format are accepted
    And Values exceeding maximum decimal places are rejected or flagged
