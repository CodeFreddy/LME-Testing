Feature: Consideration on Favorable MTM
  SR-IMHK-3_2_5_2-01
  # paragraph_ids: IMHK-3_2_5_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_2-01-positive-01
  Scenario: Calculate favorable MTM and derive net margin
    Given Market value portfolio is -300,550,000 HKD
    And Contract value portfolio is -287,850,000 HKD
    And Rounded aggregated market-risk-component margin is 46,930,000 HKD
    When Favorable MTM is calculated using the formula
    And Net margin is derived by deducting favorable MTM from rounded aggregated margin
    Then Favorable MTM (or MTM requirement) equals Market valuePortfolio - Contract valuePortfolio = -12,700,000
    And The negative number refers to a MTM requirement with absolute value 12,700,000
    And Favorable MTM is zero in this case
    And Net margin equals Maximum(0, 46,930,000 - 0) = 46,930,000

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_2-01-boundary-01
  Scenario: Net margin when favorable MTM equals rounded aggregated margin
    Given Rounded aggregated market-risk-component margin is 46,930,000 HKD
    And Favorable MTM is 46,930,000 HKD
    When Net margin is calculated using Maximum(0, Rounded aggregated margin – Favorable MTM)
    Then Net margin equals Maximum(0, 46,930,000 - 46,930,000) = 0

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_2-01-data_validation-01
  Scenario: Validate portfolio market value and contract value inputs
    Given A clearing participant has positions with HKD equivalent contract values and market values
    When The system validates and aggregates portfolio values for favorable MTM calculation
    Then Market valuePortfolio is aggregated from HKD equivalent market values
    And Contract valuePortfolio is aggregated from HKD equivalent contract values
    And Numbers are rounded off on position level
    And Multi-currency positions follow Appendix 4.6 calculation logic
