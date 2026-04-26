Feature: Corporate Action Contract Value Calculation
  SR-MR-004-E-5
  # paragraph_ids: MR-004-E-5
  Corporate Action Contract Value Calculation

  @positive @priority_high  # TC-SR-MR-004-E-5-positive-01
  Scenario: Contract value calculated as quantity times cash dividend amount
    Given A stock position exists with an original quantity
    And A cash dividend amount is defined for the corporate action
    When Corporate action adjustment is processed
    Then Contract value equals original stock position quantity times cash dividend amount

  @negative @priority_high  # TC-SR-MR-004-E-5-negative-01
  Scenario: Corporate action adjustment fails with missing quantity or dividend amount
    Given A stock position exists with missing or null quantity
    And Or a cash dividend amount is missing or null
    When Corporate action adjustment is processed
    Then Processing fails with a validation error
    And Contract value is not calculated

  @data_validation @priority_high  # TC-SR-MR-004-E-5-data_validation-01
  Scenario: Contract value calculation result matches expected formula output
    Given A stock position with quantity 400
    And A cash dividend amount per share
    When Corporate action adjustment is processed
    Then Contract value equals quantity multiplied by cash dividend amount
    And Result matches expected value from formula
