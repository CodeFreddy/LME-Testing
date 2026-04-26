Feature: Total MTM and Margin Requirement Calculation
  SR-MR-012-A-9
  # paragraph_ids: MR-012-A-9
  Total MTM and Margin Requirement Calculation

  @positive @priority_high  # TC-SR-MR-012-A-9-positive-01
  Scenario: Calculate total MTM and margin requirement with all components
    Given All margin components are available: Net margin after credit, MTM requirement, Position limit add-on, Credit risk add-on, Ad-hoc add-on
    When The total MTM and margin requirement calculation is performed
    Then The total equals Net margin after credit + MTM requirement + Position limit add-on + Credit risk add-on + Ad-hoc add-on
    And The calculated total is returned

  @boundary @priority_high  # TC-SR-MR-012-A-9-boundary-01
  Scenario: Calculate margin with zero ad-hoc add-on
    Given Net margin after credit is 41,930,000
    And MTM requirement is 12,700,000
    And Position limit add-on is 490,481
    And Credit risk add-on is 12,000,000
    And Ad-hoc add-on is 0
    When The total MTM and margin requirement calculation is performed
    Then The total equals 67,120,481 (sum excluding ad-hoc add-on)
    And The calculation correctly handles zero-value component

  @data_validation @priority_high  # TC-SR-MR-012-A-9-data_validation-01
  Scenario: Validate all margin components are present for calculation
    Given A margin calculation request is submitted
    And The calculation requires all five components
    When The system validates input data before calculation
    Then Net margin after credit is present and numeric
    And MTM requirement is present and numeric
    And Position limit add-on is present and numeric
    And Credit risk add-on is present and numeric
    And Ad-hoc add-on is present and numeric
    And Calculation proceeds only if all components are valid
