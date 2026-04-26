Feature: SVaR Scenario Data Processing
  SR-MR-002-B9-1
  # paragraph_ids: MR-002-B9-1
  SVaR Scenario Data Processing

  @positive @priority_high  # TC-SR-MR-002-B9-1-positive-01
  Scenario: Process valid SVaR scenario records with correct scenario count
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And The file contains FieldType 2 records for SVaR Scenarios
    And SVaR_Scen_Count is set to 1018
    When The system processes the FieldType 2 records for instrument 700 with 1018 scenario return values
    Then The SVaR scenario returns are successfully parsed
    And The total number of scenarios matches SVaR_Scen_Count (1018)
    And The processing result is available for margin calculation

  @boundary @priority_high  # TC-SR-MR-002-B9-1-boundary-01
  Scenario: Validate SVaR confidence level at specified boundary value
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And SVaR_CL field is present in the file header
    When The system reads SVaR_CL value of 0.98 (98% confidence level)
    Then The confidence level is accepted as valid
    And The SVaR calculation uses the 98% confidence level
    And No validation error is raised for the boundary value

  @data_validation @priority_high  # TC-SR-MR-002-B9-1-data_validation-01
  Scenario: Validate SVaR scenario return data format and precision
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And FieldType 2 records contain scenario return values for SVaR component
    When The system validates scenario return values such as 0.041026, 0.092873, 0.067737 for instrument 700
    Then Each scenario return value is validated against DECIMALS(X,10) format
    And Invalid format values are rejected with appropriate error message
    And Valid values are accepted for SVaR margin calculation
