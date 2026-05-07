Feature: Flat Rate Margin Calculation
  SR-IMHK-3_2_4_2-01
  # paragraph_ids: IMHK-3_2_4_2-01

  @positive @priority_high  # TC-SR-IMHK-3_2_4_2-01-positive-01
  Scenario: Flat rate margin calculated with higher of long or short positions included
    Given A clearing participant has positions in sub-margin groups defined on HKEX website
    And Sub-group 1 contains long positions with total absolute market value of 30,000,000 HKD and short positions with total absolute market value of 60,000,000 HKD
    And Flat margin rates are defined under FieldType 3
    And A flat rate margin multiplier of 2 is assigned per DWH0081C report
    When The flat rate margin calculation is performed following Step 1, Step 2, and Step 3
    Then All short sub-group 1 positions are included in flat rate margin calculation
    And All long sub-group 1 positions are excluded from flat rate margin calculation
    And Flat rate margin after applying margin multiplier equals 15,180,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_4_2-01-boundary-01
  Scenario: Flat rate margin when long and short absolute market values are equal
    Given A clearing participant has positions in a sub-margin group
    And Total absolute market value of long positions equals total absolute market value of short positions at exactly 50,000,000 HKD each
    When The flat rate margin calculation compares long and short absolute market values for the sub-margin group
    Then The system determines which side to include based on tie-breaking rules defined by HKEX

  @data_validation @priority_high  # TC-SR-IMHK-3_2_4_2-01-data_validation-01
  Scenario: Flat rate margin calculation validates required input data
    Given A clearing participant submits positions for flat rate margin calculation
    When The system validates input data including positions identified per §3.2.2, sub-margin groups from HKEX website, flat margin rates under FieldType 3, and margin multiplier from DWH0081C report
    Then All required data elements are validated as present and correctly formatted
    And Position identification per §3.2.2 is confirmed
    And Sub-margin group assignments are validated against HKEX website definitions
    And Flat margin rates under FieldType 3 are retrieved successfully
    And Margin multiplier from DWH0081C report is retrieved successfully
