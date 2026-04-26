Feature: Initial Margin Risk Parameter File Processing
  SR-MR-002-B20-1
  # paragraph_ids: MR-002-B20-1
  Initial Margin Risk Parameter File Processing

  @positive @priority_high  # TC-SR-MR-002-B20-1-positive-01
  Scenario: IMRPF file processed with all seven FieldType records
    Given An Initial Margin Risk Parameter File (IMRPF) is received
    And The file contains header fields Valuation_DT, HVaR_WGT, SVaR_WGT, HVaR_Scen_Count, SVaR_Scen_Count, STV_Count, HVaR_CL, SVaR_CL, HVaR_Measure, SVaR_Measure, Rounding, and Holiday_Factor
    And The file contains FieldType records 1 through 7 with valid data
    When The system processes the IMRPF file
    Then All FieldType records are parsed and validated successfully
    And Instrument price returns for HVaR and SVaR scenarios are available for margin calculation
    And Processing result is not null

  @boundary @priority_high  # TC-SR-MR-002-B20-1-boundary-01
  Scenario: IMRPF processed with HVaR and SVaR weights at specified values
    Given An IMRPF file is received with HVaR_WGT = 0.75
    And The file has SVaR_WGT = 0.25
    And The weights sum to 1.0 as expected for the weighted average calculation
    When The system processes the IMRPF file and applies the weighting parameters
    Then The HVaR component is weighted at 75%
    And The SVaR component is weighted at 25%
    And The weighted average margin calculation proceeds without validation error

  @data_validation @priority_high  # TC-SR-MR-002-B20-1-data_validation-01
  Scenario: IMRPF rejected when FieldType value is outside valid range
    Given An IMRPF file is received
    And The file contains a FieldType value of 8 (outside valid range 1-7)
    When The system validates the IMRPF file structure
    Then The file is rejected with a validation error
    And Error message indicates invalid FieldType value
