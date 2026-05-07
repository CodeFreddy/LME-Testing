Feature: Flat Rate Margin Calculation
  SR-IMHK-3_2_4_2-01
  # paragraph_ids: IMHK-3_2_4_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_4_2-01-positive-01
  Scenario: Flat rate margin calculation with higher short market value
    Given Positions are identified per §3.2.2 with sub-margin groups defined on HKEX website
    And Sub-group 1 contains long positions with total absolute market value of 30,000,000 HKD
    And Sub-group 1 contains short positions with total absolute market value of 60,000,000 HKD
    When Flat rate margin calculation is performed for sub-group 1
    Then All short sub-group 1 positions are included in the flat rate margin calculation
    And All long sub-group 1 positions are excluded from the flat rate margin calculation
    And The product of absolute position market value and flat margin rate is summed
    And Flat rate margin multiplier is applied to obtain final flat rate margin

  @boundary @priority_high  # TC-SR-IMHK-3_2_4_2-01-boundary-01
  Scenario: Flat rate margin with zero market value on one side
    Given Sub-group 2 contains long positions with total absolute market value of 750,000 HKD
    And Sub-group 2 contains short positions with total absolute market value of 0 HKD
    When Flat rate margin calculation compares long and short market values for sub-group 2
    Then All long sub-group 2 positions are included in the flat rate margin calculation
    And Short positions with zero market value are excluded

  @data_validation @priority_high  # TC-SR-IMHK-3_2_4_2-01-data_validation-01
  Scenario: Flat rate margin calculation validates required position data
    Given Position data is submitted for flat rate margin calculation
    And Positions are identified per instructions in §3.2.2
    When Flat rate margin calculation is performed
    Then Each position has valid InstrumentID
    And Each position has valid Quantity with sign indicating long (>=0) or short (<0)
    And Each position has valid absolute market value in HKD equivalent
    And Positions are correctly assigned to sub-margin groups defined on HKEX website
