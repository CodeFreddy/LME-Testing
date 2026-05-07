Feature: Flat Rate Margin Calculation
  SR-IMHK-3_2_4_2-01
  # paragraph_ids: IMHK-3_2_4_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_4_2-01-positive-01
  Scenario: Calculate flat rate margin with higher short market value in sub-group
    Given A clearing participant has positions in multiple sub-margin groups
    And Sub-group 1 has total absolute long market value of 30,000,000 HKD and total absolute short market value of 60,000,000 HKD
    And Sub-group 2 has total absolute long market value of 750,000 HKD and total absolute short market value of 0 HKD
    And Sub-group 3 has total absolute long market value of 0 HKD and total absolute short market value of 300,000 HKD
    And Flat margin rates are 12% for sub-group 1, 30% for sub-group 2, 55% for sub-group 3
    And A flat rate margin multiplier of 2 is assigned
    When The flat rate margin calculation is performed following Steps 1-3
    Then All short sub-group 1 positions are included in the calculation
    And All long sub-group 1 positions are excluded from the calculation
    And All long sub-group 2 positions are included in the calculation
    And All short sub-group 3 positions are included in the calculation
    And Flat rate margin after applying margin multiplier equals 15,180,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_4_2-01-boundary-01
  Scenario: Flat rate margin with equal long and short market values in sub-group
    Given A clearing participant has positions in a sub-margin group
    And Total absolute long market value equals total absolute short market value at 50,000,000 HKD each
    When The flat rate margin Step 1 comparison is performed
    Then The system determines which positions to include based on the tie-breaking rule
    And The calculation proceeds to Step 2 with the determined position set

  @data_validation @priority_high  # TC-SR-IMHK-3_2_4_2-01-data_validation-01
  Scenario: Validate sub-margin group classification and market value inputs
    Given A clearing participant has multiple positions across different instruments
    And Each position has an InstrumentID, Quantity, and market value in HKD equivalent
    When Positions are identified and classified per §3.2.2 instructions
    And Positions are grouped into sub-margin groups as defined on HKEX website
    Then Each position is assigned to the correct sub-margin group
    And Absolute market value of long positions is aggregated separately from short positions
    And Market values are converted to HKD equivalent where necessary
