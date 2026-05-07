Feature: Feature SR-IMHK-3_2_5_3-01
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: p-SR-IMHK-3_2_5_3-01
  Validates behavior described in SR-IMHK-3_2_5_3-01.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-1
  Scenario: Positive scenario
    Given Given the system is ready for SR-IMHK-3_2_5_3-01
    When When I perform action for SR-IMHK-3_2_5_3-01
    Then Then result is as expected for SR-IMHK-3_2_5_3-01

  @negative  # TC-SR-IMHK-3_2_5_3-01-2
  Scenario: Negative scenario
    Given Given the system is ready for SR-IMHK-3_2_5_3-01
    When When I perform action for SR-IMHK-3_2_5_3-01
    Then Then result is as expected for SR-IMHK-3_2_5_3-01
