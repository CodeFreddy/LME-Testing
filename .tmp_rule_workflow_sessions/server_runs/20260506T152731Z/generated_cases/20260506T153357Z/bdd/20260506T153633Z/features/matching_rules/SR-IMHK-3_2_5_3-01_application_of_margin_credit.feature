Feature: Application of Margin Credit
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: IMHK-3_2_5_3-01
  Validates that margin credit is correctly applied to calculate net margin after credit for clearing participants.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-positive-01
  Scenario: Apply margin credit to calculate net margin after credit
    Given a clearing participant has a net margin of 46,930,000 HKD
    And the margin credit granted is 5,000,000 HKD
    When the system calculates net margin after credit using the formula Maximum[0, (Net margin - Margin credit)]
    Then net margin after credit is calculated as Maximum[0, (46,930,000 - 5,000,000)] = 41,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_3-01-boundary-01
  Scenario: Boundary case when net margin equals margin credit
    Given a clearing participant has a net margin of 5,000,000 HKD
    And the margin credit granted is 5,000,000 HKD
    When the system calculates net margin after credit using the formula Maximum[0, (Net margin - Margin credit)]
    And the subtraction result equals zero
    Then net margin after credit is calculated as Maximum[0, 0] = 0

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_3-01-data_validation-01
  Scenario: Validate margin credit is granted to each clearing participant
    Given a clearing participant is registered in the system
    And the standard margin credit value is 5,000,000 HKD
    When the system applies margin credit for margin calculation
    Then the margin credit of 5,000,000 is granted to the clearing participant
    And the margin credit is applied in the net margin after credit calculation
