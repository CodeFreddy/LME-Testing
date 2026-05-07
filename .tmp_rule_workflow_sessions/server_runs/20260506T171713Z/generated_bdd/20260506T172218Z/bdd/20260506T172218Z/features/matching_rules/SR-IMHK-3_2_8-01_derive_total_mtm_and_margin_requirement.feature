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
    When Total MTM and margin requirement is calculated by adding net margin after credit to other risk components
    Then Total MTM and margin requirement equals 41,930,000 + 12,700,000 + 487,332 + 12,000,000 + 600,000 = 67,717,332 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_8-01-boundary-01
  Scenario: Total margin requirement with zero other risk components
    Given Net margin after credit is 50,000,000 HKD
    And MTM requirement is 0 HKD
    And Position limit add-on is 0 HKD
    And Credit risk add-on is 0 HKD
    And Ad-hoc add-on is 0 HKD
    When Total MTM and margin requirement is calculated
    Then Total MTM and margin requirement equals 50,000,000 + 0 + 0 + 0 + 0 = 50,000,000 HKD
    And Total equals net margin after credit when no other risk components apply

  @data_validation @priority_high  # TC-SR-IMHK-3_2_8-01-data_validation-01
  Scenario: Validate all risk components are present for total calculation
    Given A clearing participant has completed margin calculations per §3.2.5 and §3.2.6
    And Risk components include Net margin after credit, MTM requirement, Position limit add-on, Credit risk add-on, and Ad-hoc add-on
    When Total MTM and margin requirement is derived from results under §3.2.5 and §3.2.6
    Then Net margin after credit is validated as present and numeric
    And MTM requirement is validated as present and numeric
    And Position limit add-on is validated as present and numeric
    And Credit risk add-on is validated as present and numeric
    And Ad-hoc add-on is validated as present and numeric
