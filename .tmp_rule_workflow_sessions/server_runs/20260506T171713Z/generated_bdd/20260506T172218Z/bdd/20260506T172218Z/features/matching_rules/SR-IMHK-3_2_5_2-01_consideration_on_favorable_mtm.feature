Feature: Consideration on Favorable MTM
  SR-IMHK-3_2_5_2-01
  # paragraph_ids: IMHK-3_2_5_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_2-01-positive-01
  Scenario: Calculate favorable MTM and derive net margin
    Given Market value of portfolio is -300,550,000 HKD
    And Contract value of portfolio is -287,850,000 HKD
    And Rounded aggregated market-risk-component margin is 46,930,000 HKD
    When Step 1 calculates favorable MTM using the formula
    And Step 2 deducts favorable MTM from rounded aggregated margin
    Then Favorable MTM equals -12,700,000 HKD (negative indicates MTM requirement)
    And Favorable MTM is zero when result is negative
    And Net margin equals Maximum(0, 46,930,000 - 0) = 46,930,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_2-01-boundary-01
  Scenario: Net margin at zero when favorable MTM equals aggregated margin
    Given Rounded aggregated market-risk-component margin is 50,000,000 HKD
    And Favorable MTM is 50,000,000 HKD
    When Step 2 calculates net margin using Maximum(0, Rounded aggregated margin – Favorable MTM)
    Then Net margin equals Maximum(0, 50,000,000 - 50,000,000) = 0 HKD

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_2-01-data_validation-01
  Scenario: Validate portfolio market value and contract value inputs
    Given A clearing participant has a portfolio with positions
    And Portfolio has aggregated HKD equivalent market value and contract value
    When Step 1 calculates favorable MTM using Market valuePortfolio - Contract valuePortfolio
    Then Market valuePortfolio is validated as a numeric value
    And Contract valuePortfolio is validated as a numeric value
    And Both values are aggregated HKD equivalent values
    And Favorable MTM and MTM requirement are mutually exclusive
