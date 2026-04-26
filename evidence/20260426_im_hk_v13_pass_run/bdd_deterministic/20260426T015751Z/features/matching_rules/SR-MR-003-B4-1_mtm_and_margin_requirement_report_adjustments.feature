Feature: MTM and Margin Requirement Report Adjustments
  SR-MR-003-B4-1
  # paragraph_ids: MR-003-B4-1
  MTM and Margin Requirement Report Adjustments

  @positive @priority_high  # TC-SR-MR-003-B4-1-positive-01
  Scenario: Margin calculation with all MTM Report adjustments applied
    Given MTM and Margin Requirement Report contains: Consideration on favorable MTM, Application of margin credit, Other risk component MTM requirement, Position limit add-on, Credit risk add-on, Ad-hoc add-on
    When The system calculates total MTM and margin requirement
    Then All margin adjustments from MTM Report are incorporated
    And Calculated value is available

  @boundary @priority_high  # TC-SR-MR-003-B4-1-boundary-01
  Scenario: Margin calculation with contract value at threshold boundary
    Given A position with InstrumentID is provided
    And Contract value is set to a large threshold value (e.g., $384,000,000 HKD equivalent)
    When The system calculates total MTM and margin requirement
    Then The calculation processes the contract value correctly
    And Result reflects appropriate margin for large contract value

  @data_validation @priority_high  # TC-SR-MR-003-B4-1-data_validation-01
  Scenario: Margin calculation rejected when market value is invalid format
    Given Position data is received from Marginable Position Report (RMAMP01)
    And Market value field contains non-numeric or invalid HKD equivalent value
    When The system validates required position details for margin calculation
    Then Validation fails with error indicating invalid market value format
    And Margin calculation does not proceed
