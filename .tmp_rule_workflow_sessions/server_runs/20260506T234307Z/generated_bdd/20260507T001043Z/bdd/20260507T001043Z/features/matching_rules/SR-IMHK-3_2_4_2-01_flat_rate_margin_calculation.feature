Feature: Flat Rate Margin Calculation
  SR-IMHK-3_2_4_2-01
  # paragraph_ids: IMHK-3_2_4_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_4_2-01-positive-01
  Scenario: Calculate flat rate margin with complete three-step process across multiple sub-margin groups
    Given A clearing participant has positions identified per §3.2.2 across multiple sub-margin groups
    And Sub-group 1 positions: total absolute long market value is 30,000,000 HKD, total absolute short market value is 60,000,000 HKD
    And Sub-group 2 positions: total absolute long market value is 750,000 HKD, total absolute short market value is 0 HKD
    And Sub-group 3 positions: total absolute long market value is 0 HKD, total absolute short market value is 300,000 HKD
    And Flat margin rates under FieldType 3 are: 12% for sub-group 1, 30% for sub-group 2, 55% for sub-group 3
    And Flat rate margin multiplier of 2 is assigned per Daily Participant Margin Multiplier Report (DWH0081C)
    When Step 1: System aggregates and compares total absolute market values of long vs short positions for each sub-margin group
    And Step 1: System includes sub-group 1 short positions (60,000,000 HKD), sub-group 2 long positions (750,000 HKD), and sub-group 3 short positions (300,000 HKD) in calculation
    And Step 2: System sums the product of absolute position market value and flat margin rate for each included position
    And Step 3: System applies the flat rate margin multiplier of 2
    Then Sub-group 1: short positions included (60,000,000 HKD), long positions excluded because short absolute value is higher
    And Sub-group 2: long positions included (750,000 HKD), short positions excluded because long absolute value is higher
    And Sub-group 3: short positions included (300,000 HKD), long positions excluded because short absolute value is higher
    And Flat rate margin after applying margin multiplier equals (60,000,000 × 12% + 750,000 × 30% + 300,000 × 55%) × 2 = 15,180,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_4_2-01-boundary-01
  Scenario: Flat rate margin when long and short market values are equal in sub-group
    Given A clearing participant has positions in a sub-margin group
    And Total absolute long market value equals total absolute short market value (e.g., both are 50,000,000 HKD)
    When Flat rate margin calculation compares long and short market values for the sub-group
    Then The system determines which positions to include based on the comparison result
    And Flat rate margin calculation proceeds to Step 2 with the determined positions

  @data_validation @priority_high  # TC-SR-IMHK-3_2_4_2-01-data_validation-01
  Scenario: Validate position identification and sub-margin group assignment
    Given A clearing participant submits position data for margin calculation
    And Positions include instrument IDs with quantities and market values
    When The system processes positions for flat rate margin calculation
    Then Each position is identified per instructions in §3.2.2
    And Each position is assigned to the correct sub-margin group as defined on HKEX website
    And Absolute market values are calculated in HKD equivalent for long and short positions separately
