Feature: Flat Rate Margin Scenario Count Validation
  SR-MR-002-B5-1
  # paragraph_ids: MR-002-B5-1
  Flat Rate Margin Scenario Count Validation

  @positive @priority_high  # TC-SR-MR-002-B5-1-positive-01
  Scenario: Scenario count matches SVaR_Scen_Count for FieldType 3
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And The SVaR_Scen_Count parameter is set to a specific value (e.g., 1018)
    When FieldType 3 records (Flat Rate Scenarios) are parsed
    And The total number of scenario columns is counted
    Then The total number of scenarios equals the SVaR_Scen_Count value
    And The file is accepted for processing

  @negative @priority_high  # TC-SR-MR-002-B5-1-negative-01
  Scenario: Scenario count mismatch with SVaR_Scen_Count for FieldType 3
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And The SVaR_Scen_Count parameter is set to a specific value (e.g., 1018)
    When FieldType 3 records (Flat Rate Scenarios) are parsed
    And The total number of scenario columns differs from SVaR_Scen_Count
    Then A validation error is raised
    And The file is rejected with an appropriate error message

  @data_validation @priority_high  # TC-SR-MR-002-B5-1-data_validation-01
  Scenario: FieldType 3 return values format validation
    Given An Initial Margin Risk Parameter File (IMRPF) is being processed
    And FieldType 3 records (Flat Rate Scenarios) are present
    When Return values for each instrument in flat rate margin component are parsed
    Then Each return value conforms to DECIMALS(X,10) format
    And Values with more than 10 decimal places are either rejected or truncated per system rules
