Feature: HVaR Scenario Data Processing
  SR-MR-002-B8-1
  # paragraph_ids: MR-002-B8-1
  HVaR Scenario Data Processing

  @positive @priority_high  # TC-SR-MR-002-B8-1-positive-01
  Scenario: Process valid HVaR scenario records with correct scenario count
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And The file contains FieldType 1 records for HVaR Scenarios
    And HVaR_Scen_Count is set to 1000
    When The system processes the FieldType 1 records for instrument 700 with 1000 scenario return values
    Then The HVaR scenario returns are successfully parsed
    And The total number of scenarios matches HVaR_Scen_Count (1000)
    And The processing result is available for margin calculation

  @boundary @priority_high  # TC-SR-MR-002-B8-1-boundary-01
  Scenario: Validate HVaR confidence level at specified boundary value
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And HVaR_CL field is present in the file header
    When The system reads HVaR_CL value of 0.994 (99.4% confidence level)
    Then The confidence level is accepted as valid
    And The HVaR calculation uses the 99.4% confidence level
    And No validation error is raised for the boundary value

  @data_validation @priority_high  # TC-SR-MR-002-B8-1-data_validation-01
  Scenario: Validate HVaR scenario return data format and precision
    Given The Initial Margin Risk Parameter File (IMRPF) is available for processing
    And FieldType 1 records contain scenario return values for HVaR component
    When The system validates scenario return values such as 0.01391, 0.01422, 0.006132 for instrument 700
    Then Each scenario return value is validated against DECIMALS(X,10) format
    And Invalid format values are rejected with appropriate error message
    And Valid values are accepted for HVaR margin calculation
