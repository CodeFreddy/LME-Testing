Feature: Application of Margin Credit
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: IMHK-3_2_5_3-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-positive-01
  Scenario: Apply margin credit to net margin calculation
    Given Net margin is 46,930,000 HKD
    And Margin credit of 5,000,000 HKD is granted to the clearing participant
    When Net margin after credit is calculated using Maximum[0, (Net margin – Margin credit)]
    Then Net margin after credit equals Maximum[0, (46,930,000 – 5,000,000)] = 41,930,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_3-01-boundary-01
  Scenario: Net margin after credit at zero boundary
    Given Net margin is 5,000,000 HKD
    And Margin credit is 5,000,000 HKD
    When Net margin after credit is calculated using Maximum[0, (Net margin – Margin credit)]
    Then Net margin after credit equals Maximum[0, (5,000,000 – 5,000,000)] = 0 HKD

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_3-01-data_validation-01
  Scenario: Validate margin credit value for clearing participant
    Given A clearing participant is registered in the system
    And Margin credit is granted to each CP
    When Margin calculation applies the margin credit
    Then Margin credit value is retrieved for the specific clearing participant
    And Margin credit is a valid non-negative numeric value
    And Margin credit is applied correctly in the net margin after credit formula
