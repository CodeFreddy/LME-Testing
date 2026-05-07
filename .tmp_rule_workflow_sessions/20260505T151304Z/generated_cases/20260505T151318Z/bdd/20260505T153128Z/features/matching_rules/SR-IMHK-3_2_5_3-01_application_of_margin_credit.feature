Feature: Application of Margin Credit
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: IMHK-3_2_5_3-01
  Validates margin credit application and net margin calculation for clearing participants.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-positive-01
  Scenario: Calculate net margin after credit with margin exceeding credit
    Given A clearing participant has a net margin of 46,930,000
    And A margin credit of 5,000,000 is granted to the clearing participant
    When The margin credit is applied for margin calculation
    Then The net margin after credit is calculated as 41,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_3-01-boundary-01
  Scenario: Calculate net margin after credit when margin equals credit
    Given A clearing participant has a net margin of 5,000,000
    And A margin credit of 5,000,000 is granted to the clearing participant
    When The margin credit is applied for margin calculation
    Then The net margin after credit is calculated as 0

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_3-01-data_validation-01
  Scenario: Validate margin credit value applied to clearing participant
    Given A clearing participant is registered in the system
    When The margin credit is applied for margin calculation
    Then The margin credit value is validated as 5,000,000
    And The margin credit is granted to the clearing participant
