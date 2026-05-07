Feature: Application of Margin Credit
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: IMHK-3_2_5_3-01
  Validates margin credit application and net margin after credit calculation for clearing participants.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-positive-01
  Scenario: Calculate net margin after applying margin credit
    Given a clearing participant with net margin of 46,930,000
    And margin credit of 5,000,000 granted to the CP
    When the system calculates net margin after credit using Maximum[0, (Net margin – Margin credit)]
    Then net margin after credit equals Maximum[0, (46,930,000 – 5,000,000)]
    And net margin after credit equals 41,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_3-01-boundary-01
  Scenario: Calculate net margin after credit when net margin equals margin credit
    Given a clearing participant with net margin of 5,000,000
    And margin credit of 5,000,000 granted to the CP
    When the system calculates net margin after credit using Maximum[0, (Net margin – Margin credit)]
    Then net margin after credit equals Maximum[0, (5,000,000 – 5,000,000)]
    And net margin after credit equals 0

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_3-01-data_validation-01
  Scenario: Validate margin credit is granted to each clearing participant
    Given a clearing participant registered in the system
    When the system validates margin credit assignment for the CP
    Then margin credit is granted to each CP
    And margin credit value is normally 5,000,000
    And margin credit is applied for margin calculation
