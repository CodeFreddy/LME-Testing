Feature: Initial Margin Risk Parameter File Layout
  SR-MR-002-B3-1
  # paragraph_ids: MR-002-B3-1
  Initial Margin Risk Parameter File Layout

  @positive @priority_high  # TC-SR-MR-002-B3-1-positive-01
  Scenario: Process valid IMRPF with all required field types
    Given An Initial Margin Risk Parameter File (RPF01) with all required header fields
    And FieldType records 1 through 7 are present with valid data
    When The system processes the IMRPF file for margin calculation
    Then All FieldType records are parsed and validated successfully
    And Instrument price returns for HVaR and SVaR scenarios are available for calculation

  @boundary @priority_high  # TC-SR-MR-002-B3-1-boundary-01
  Scenario: Validate HVaR and SVaR scenario count boundaries
    Given An Initial Margin Risk Parameter File with header parameters
    And HVaR_Scen_Count is set to 1000
    And SVaR_Scen_Count is set to 1018
    When The system validates the scenario counts against the actual scenario data columns
    Then The total number of FieldType 1 scenarios matches HVaR_Scen_Count value of 1000
    And The total number of FieldType 2 scenarios matches SVaR_Scen_Count value of 1018

  @data_validation @priority_high  # TC-SR-MR-002-B3-1-data_validation-01
  Scenario: Validate FieldType enumeration values
    Given An Initial Margin Risk Parameter File with FieldType records
    And FieldType values must be integers from 1 to 7
    When The system validates each FieldType value in the file
    Then FieldType 1 is accepted as HVaR Scenarios
    And FieldType 2 is accepted as SVaR Scenarios
    And FieldType 3 is accepted as Flat Rate Scenarios
    And FieldType 4 is accepted as Beta hedge information
    And FieldType 5 is accepted as Instrument delta information
    And FieldType 6 is accepted as Price threshold and add-on%
    And FieldType 7 is accepted as Corporate action position margin scenarios
