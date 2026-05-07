Feature: Total MTM and Margin Requirement Calculation
  SR-IMHK-3_2_8-01
  # paragraph_ids: IMHK-3_2_8-01
  Validates that total MTM and margin requirement is correctly derived by summing net margin after credit and all other risk components.

  @positive @priority_high  # TC-SR-IMHK-3_2_8-01-positive-01
  Scenario: Calculate total MTM and margin requirement with all components
    Given net margin after credit is calculated as 41,930,000
    And MTM requirement is 12,700,000
    And position limit add-on is 487,332
    And credit risk add-on is 12,000,000
    And ad-hoc add-on is 600,000
    When the system derives total MTM and margin requirement by adding net margin after credit to other risk components
    Then total MTM and margin requirement equals 67,717,332

  @boundary @priority_high  # TC-SR-IMHK-3_2_8-01-boundary-01
  Scenario: Calculate total MTM and margin requirement when credit risk add-on is not applicable
    Given net margin after credit is calculated as 41,930,000
    And MTM requirement is 12,700,000
    And position limit add-on is 487,332
    And credit risk add-on is not applicable due to VaR Platform launch
    And ad-hoc add-on is 600,000
    When the system derives total MTM and margin requirement with credit risk add-on set to zero
    Then total MTM and margin requirement equals 55,717,332 (excluding credit risk add-on)

  @data_validation @priority_high  # TC-SR-IMHK-3_2_8-01-data_validation-01
  Scenario: Validate all required risk components are present for total MTM calculation
    Given a clearing participant has positions requiring margin calculation
    And results from §3.2.5 and §3.2.6 calculations are available
    When the system validates that all required components are present: net margin after credit, MTM requirement, position limit add-on, credit risk add-on, and ad-hoc add-on
    Then validation confirms all components are present with valid numeric format
    And calculation proceeds to derive total MTM and margin requirement
