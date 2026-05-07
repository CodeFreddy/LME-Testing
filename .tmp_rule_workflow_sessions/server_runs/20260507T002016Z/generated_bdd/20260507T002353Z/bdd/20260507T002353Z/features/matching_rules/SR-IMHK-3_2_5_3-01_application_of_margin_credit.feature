Feature: Application of Margin Credit
  SR-IMHK-3_2_5_3-01
  # paragraph_ids: IMHK-3_2_5_3-01
  Validates the correct application of margin credit to calculate net margin after credit using the Maximum formula, including boundary conditions and data validation.

  @positive @priority_high  # TC-SR-IMHK-3_2_5_3-01-positive-01
  Scenario: Apply margin credit to calculate net margin after credit
    Given Net margin before credit is 46,930,000
    And Margin credit is 5,000,000
    When the system calculates net margin after credit
    And the system applies the Maximum[0, (Net margin – Margin credit)] formula
    Then net margin after credit is calculated as 41,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_3-01-boundary-01
  Scenario: Net margin after credit when net margin equals margin credit
    Given Net margin before credit is exactly 5,000,000
    And Margin credit is 5,000,000
    When the system calculates net margin after credit
    And the system applies the Maximum[0, (Net margin – Margin credit)] formula
    Then net margin after credit is 0
    And the Maximum function ensures the result is not negative

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_3-01-data_validation-01
  Scenario: Validate margin credit value and Maximum function application
    Given A clearing participant with margin calculation request
    When the system validates the margin credit value
    And the system validates the Maximum function logic for net margin calculation
    Then margin credit is a valid positive numeric value
    And the Maximum[0, (Net margin – Margin credit)] formula is correctly implemented
    And net margin after credit is never negative regardless of input values
