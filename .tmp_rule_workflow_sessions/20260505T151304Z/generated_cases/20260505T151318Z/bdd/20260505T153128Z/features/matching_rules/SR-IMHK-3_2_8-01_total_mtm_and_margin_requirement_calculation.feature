Feature: Total MTM and Margin Requirement Calculation
  SR-IMHK-3_2_8-01
  # paragraph_ids: IMHK-3_2_8-01
  Validates that total MTM and margin requirement is correctly derived by summing net margin after credit and all other risk components.

  @positive @priority_high  # TC-SR-IMHK-3_2_8-01-positive-01
  Scenario: Calculate total MTM and margin requirement with all components
    Given Net margin after credit value is available (e.g., 41,930,000)
    And MTM requirement value is available (e.g., 12,700,000)
    And Position limit add-on value is available (e.g., 487,332)
    And Credit risk add-on value is available (e.g., 12,000,000)
    And Ad-hoc add-on value is available (e.g., 600,000)
    When The system derives total MTM and margin requirement
    Then Total MTM and margin requirement equals the sum of all components (e.g., 67,717,332)

  @boundary @priority_high  # TC-SR-IMHK-3_2_8-01-boundary-01
  Scenario: Calculate total MTM and margin requirement when credit risk add-on is not applicable
    Given VaR Platform has been launched
    And Credit risk add-on is not applicable (value is 0)
    And All other risk components have valid values
    When The system derives total MTM and margin requirement
    Then Total MTM and margin requirement equals the sum of all applicable components excluding credit risk add-on

  @data_validation @priority_high  # TC-SR-IMHK-3_2_8-01-data_validation-01
  Scenario: Validate margin requirement calculation with missing component values
    Given One or more margin component values are missing or null
    And The calculation request is submitted for total MTM and margin requirement
    When The system attempts to derive total MTM and margin requirement
    Then The calculation is rejected
    And An appropriate validation error is returned indicating missing or invalid component data
