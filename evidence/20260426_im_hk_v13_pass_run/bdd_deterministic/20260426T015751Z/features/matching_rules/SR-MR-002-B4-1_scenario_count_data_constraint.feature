Feature: Scenario Count Data Constraint
  SR-MR-002-B4-1
  # paragraph_ids: MR-002-B4-1
  Scenario Count Data Constraint

  @positive @priority_high  # TC-SR-MR-002-B4-1-positive-01
  Scenario: Accept IMRPF when scenario count matches HVaR_Scen_Count
    Given An Initial Margin Risk Parameter File with HVaR_Scen_Count header set to a specific value
    And FieldType 1 records with scenario returns for each instrument
    When The total number of scenario columns in FieldType 1 matches the HVaR_Scen_Count value
    Then The file passes validation
    And The scenario returns are processed for HVaR component calculation

  @negative @priority_high  # TC-SR-MR-002-B4-1-negative-01
  Scenario: Reject IMRPF when scenario count mismatches HVaR_Scen_Count
    Given An Initial Margin Risk Parameter File with HVaR_Scen_Count header set to a specific value
    And FieldType 1 records with a different number of scenario columns than the header specifies
    When The total number of scenario columns in FieldType 1 does not match the HVaR_Scen_Count value
    Then The file validation fails
    And An error is raised indicating scenario count mismatch

  @data_validation @priority_high  # TC-SR-MR-002-B4-1-data_validation-01
  Scenario: Validate scenario return data format for FieldType 1
    Given An Initial Margin Risk Parameter File with FieldType 1 records
    And Scenario return values for each instrument in HVaR component
    When The system validates the format of scenario return values
    Then Each scenario return value is validated as DECIMALS(X,10) format
    And Invalid non-decimal values are rejected
