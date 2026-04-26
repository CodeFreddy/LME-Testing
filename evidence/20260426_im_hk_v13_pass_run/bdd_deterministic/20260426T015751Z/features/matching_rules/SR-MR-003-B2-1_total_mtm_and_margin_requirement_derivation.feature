Feature: Total MTM and Margin Requirement Derivation
  SR-MR-003-B2-1
  # paragraph_ids: MR-003-B2-1
  Total MTM and Margin Requirement Derivation

  @positive @priority_high  # TC-SR-MR-003-B2-1-positive-01
  Scenario: Derive Total MTM and Margin Requirement from Aggregated Results
    Given Market Risk Components have been aggregated with Margin Adjustments per section 3.2.5
    And Other Risk Components have been calculated or retrieved per section 3.2.6
    When The derivation process under section 3.2.8 is executed
    Then Total MTM is derived from results under sections 3.2.5 and 3.2.6
    And Margin Requirement is derived from results under sections 3.2.5 and 3.2.6
    And Final values are produced and available for reporting

  @boundary @priority_high  # TC-SR-MR-003-B2-1-boundary-01
  Scenario: Boundary Condition for Derivation with Minimal Risk Components
    Given Market Risk Components aggregation from section 3.2.5 contains minimal values
    And Other Risk Components from section 3.2.6 contain minimal or zero values
    When The derivation process under section 3.2.8 is executed
    Then The derivation completes without error
    And Total MTM and Margin Requirement reflect the boundary condition appropriately

  @data_validation @priority_high  # TC-SR-MR-003-B2-1-data_validation-01
  Scenario: Validation of Input Results for MTM and Margin Derivation
    Given Aggregated Market Risk Components from section 3.2.5 are available
    And Other Risk Components from section 3.2.6 are available
    When The system validates the presence and integrity of results from sections 3.2.5 and 3.2.6
    Then Results from section 3.2.5 are validated for completeness
    And Results from section 3.2.6 are validated for completeness
    And Data integrity checks confirm values are within expected ranges
