Feature: MTM and Margin Requirement Report Absolute Value Display
  SR-MR-012-A-3
  # paragraph_ids: MR-012-A-3
  MTM and Margin Requirement Report Absolute Value Display

  @positive @priority_high  # TC-SR-MR-012-A-3-positive-01
  Scenario: Absolute value of favorable MTM shown in report
    Given A portfolio with a favorable MTM value
    When The MTM and Margin Requirement Report is generated
    Then The absolute value of favorable MTM is shown in the report

  @boundary @priority_high  # TC-SR-MR-012-A-3-boundary-01
  Scenario: Zero MTM value boundary in report
    Given A portfolio with MTM value of zero
    When The MTM and Margin Requirement Report is generated
    Then The absolute value of zero is shown in the report

  @data_validation @priority_high  # TC-SR-MR-012-A-3-data_validation-01
  Scenario: Negative MTM requirement converted to absolute value
    Given A portfolio with a negative MTM requirement value
    When The MTM and Margin Requirement Report is generated
    Then The absolute value of the MTM requirement is shown in the report
