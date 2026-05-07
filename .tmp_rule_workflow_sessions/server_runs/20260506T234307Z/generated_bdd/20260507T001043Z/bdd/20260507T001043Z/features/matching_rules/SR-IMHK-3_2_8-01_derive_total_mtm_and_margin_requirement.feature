Feature: Derive Total MTM and Margin Requirement
  SR-IMHK-3_2_8-01
  # paragraph_ids: IMHK-3_2_8-01

  @positive @priority_high  # TC-SR-IMHK-3_2_8-01-positive-01
  Scenario: Calculate total MTM and margin requirement from all components
    Given Net margin after credit is 41,930,000 HKD
    And MTM requirement is 12,700,000 HKD
    And Position limit add-on is 487,332 HKD
    And Credit risk add-on is 12,000,000 HKD
    And Ad-hoc add-on is 600,000 HKD
    When Total MTM and margin requirement is calculated
    Then Total MTM and margin requirement equals 41,930,000 + 12,700,000 + 487,332 + 12,000,000 + 600,000 = 67,717,332 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_8-01-boundary-01
  Scenario: Total MTM and margin requirement when other risk components are zero
    Given Net margin after credit is 41,930,000 HKD
    And MTM requirement is 0 HKD
    And Position limit add-on is 0 HKD
    And Credit risk add-on is 0 HKD
    And Ad-hoc add-on is 0 HKD
    When Total MTM and margin requirement is calculated
    Then Total MTM and margin requirement equals 41,930,000 + 0 + 0 + 0 + 0 = 41,930,000 HKD

  @data_validation @priority_high  # TC-SR-IMHK-3_2_8-01-data_validation-01
  Scenario: Validate all risk components are present for total calculation
    Given A clearing participant has completed calculations under §3.2.5 and §3.2.6
    When The system validates input data for total MTM and margin requirement calculation
    Then Net margin after credit value is present from §3.2.5.3
    And MTM requirement value is present from §3.2.5.2
    And Position limit add-on value is present
    And Credit risk add-on value is present
    And Ad-hoc add-on value is present
