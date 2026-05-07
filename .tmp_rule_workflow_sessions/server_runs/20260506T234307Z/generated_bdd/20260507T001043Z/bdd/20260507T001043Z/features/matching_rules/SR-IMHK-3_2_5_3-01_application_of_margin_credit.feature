Feature: Application of Margin Credit
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: IMHK-3_2_5_3-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-positive-01
  Scenario: Apply margin credit to calculate net margin after credit
    Given A clearing participant is granted a margin credit of 5,000,000 HKD
    And Net margin is 46,930,000 HKD
    When Net margin after credit is calculated using the formula
    Then Net margin after credit equals Maximum[0, (46,930,000 - 5,000,000)] = 41,930,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_3-01-boundary-01
  Scenario: Net margin after credit when net margin equals margin credit
    Given A clearing participant has net margin of 5,000,000 HKD
    And Margin credit is 5,000,000 HKD
    When Net margin after credit is calculated
    Then Net margin after credit equals Maximum[0, (5,000,000 - 5,000,000)] = 0 HKD

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_3-01-data_validation-01
  Scenario: Validate margin credit value for clearing participant
    Given A clearing participant submits margin calculation request
    When The system retrieves the margin credit value for the participant
    Then Margin credit is granted to each CP
    And Margin credit value is normally 5,000,000 HKD
    And Margin credit is applied for margin calculation
