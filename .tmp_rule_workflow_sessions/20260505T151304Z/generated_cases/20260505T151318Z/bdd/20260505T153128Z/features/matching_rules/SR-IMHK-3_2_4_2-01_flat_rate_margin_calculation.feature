Feature: Flat Rate Margin Calculation
  SR-IMHK-3_2_4_2-01
  # paragraph_ids: IMHK-3_2_4_2-01
  Validates flat rate margin calculation following the three-step process: aggregating positions by sub-margin group, applying flat margin rates, and applying the margin multiplier per HKEX requirements.

  @positive @priority_high  # TC-SR-IMHK-3_2_4_2-01-positive-01
  Scenario: Successful flat rate margin calculation with multiple sub-margin groups
    Given a clearing participant has positions across multiple sub-margin groups
    And sub-group 1 has long positions with total absolute market value of 30,000,000 HKD and short positions with total absolute market value of 60,000,000 HKD
    And sub-group 2 has long positions with total absolute market value of 750,000 HKD and no short positions
    And sub-group 3 has no long positions and short positions with total absolute market value of 300,000 HKD
    And flat margin rates are defined under FieldType 3 (e.g., 12%, 30%, 55%)
    And a flat rate margin multiplier of 2 is assigned per DWH0081C report
    When the flat rate margin calculation is performed
    Then the system includes only short positions for sub-group 1 (higher absolute market value)
    And the system includes only long positions for sub-group 2 (higher absolute market value)
    And the system includes only short positions for sub-group 3 (higher absolute market value)
    And the flat rate margin is calculated as (60,000,000 × 12% + 750,000 × 30% + 300,000 × 55%) × 2 = 15,180,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_4_2-01-boundary-01
  Scenario: Flat rate margin calculation when long and short absolute market values are equal
    Given a clearing participant has positions in a sub-margin group
    And the total absolute market value of long positions equals the total absolute market value of short positions (e.g., both are 50,000,000 HKD)
    And flat margin rates are defined under FieldType 3
    And a flat rate margin multiplier is assigned per DWH0081C report
    When the flat rate margin calculation is performed for this sub-margin group
    Then the system determines which positions to include based on the tie-breaking rule when long and short absolute market values are equal
    And the flat rate margin calculation proceeds with the determined position set

  @data_validation @priority_high  # TC-SR-IMHK-3_2_4_2-01-data_validation-01
  Scenario: Validation of required input data for flat rate margin calculation
    Given a clearing participant submits position data for flat rate margin calculation
    And position data includes instrument IDs, quantities, and market values
    When the submitted position data is missing required fields such as absolute market value, position direction (long/short), or sub-margin group classification
    Then the system rejects the calculation request
    And an appropriate validation error is returned indicating the missing or invalid required fields
