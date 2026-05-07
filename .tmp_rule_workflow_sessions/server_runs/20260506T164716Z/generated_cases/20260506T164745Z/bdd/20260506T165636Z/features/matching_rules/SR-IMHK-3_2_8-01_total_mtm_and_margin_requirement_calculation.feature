Feature: Total MTM and Margin Requirement Calculation
  SR-IMHK-3_2_8-01
  # paragraph_ids: IMHK-3_2_8-01
  Validates total MTM and margin requirement calculation by summing net margin after credit and all risk components.

  @positive @priority_high  # TC-SR-IMHK-3_2_8-01-positive-01
  Scenario: Calculate total MTM and margin requirement with all components
    Given net margin after credit is 41,930,000
    And MTM requirement is 12,700,000
    And position limit add-on is 487,332
    And credit risk add-on is 12,000,000
    And ad-hoc add-on is 600,000
    When the system calculates total MTM and margin requirement
    Then total MTM and margin requirement equals 67,717,332

  @boundary @priority_high  # TC-SR-IMHK-3_2_8-01-boundary-01
  Scenario: Calculate total MTM and margin requirement when credit risk add-on is not applicable
    Given net margin after credit is 41,930,000
    And MTM requirement is 12,700,000
    And position limit add-on is 487,332
    And credit risk add-on is 0 (not applicable after VaR Platform launch)
    And ad-hoc add-on is 600,000
    When the system calculates total MTM and margin requirement
    Then total MTM and margin requirement equals 55,717,332

  @data_validation @priority_high  # TC-SR-IMHK-3_2_8-01-data_validation-01
  Scenario: Reject calculation when required component value is missing
    Given net margin after credit is 41,930,000
    And MTM requirement is missing or null
    And position limit add-on is 487,332
    And credit risk add-on is 12,000,000
    And ad-hoc add-on is 600,000
    When the system attempts to calculate total MTM and margin requirement
    Then the calculation is rejected with a validation error indicating missing MTM requirement
