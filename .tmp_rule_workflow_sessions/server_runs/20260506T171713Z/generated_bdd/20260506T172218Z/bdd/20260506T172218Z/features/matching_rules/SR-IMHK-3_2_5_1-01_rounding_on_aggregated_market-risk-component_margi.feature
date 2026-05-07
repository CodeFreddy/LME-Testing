Feature: Rounding on Aggregated Market-risk-component Margin
  SR-IMHK-3_2_5_1-01
  # paragraph_ids: IMHK-3_2_5_1-01

  @positive @priority_high  # TC-SR-IMHK-3_2_5_1-01-positive-01
  Scenario: Round up aggregated margin to nearest rounding parameter
    Given Portfolio margin is 10,000,000 HKD
    And Flat rate margin is 15,180,000 HKD
    And Liquidation risk add-on is 266,865 HKD
    And Structured product add-on is 550,000 HKD
    And Corporate action position margin is 2,500,000 HKD
    And Holiday add-on is 18,433,039 HKD
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When Step 1 aggregates all market risk components
    And Step 2 rounds up the aggregated margin to the nearest 10,000
    Then Aggregated market-risk-component margin equals 46,929,904 HKD
    And Rounded aggregated market-risk-component margin equals 46,930,000 HKD

  @boundary @priority_high  # TC-SR-IMHK-3_2_5_1-01-boundary-01
  Scenario: Aggregated margin already at rounding increment boundary
    Given Aggregated market-risk-component margin is 46,930,000 HKD
    And Rounding parameter in Initial Margin Risk Parameter File is 10,000
    When Step 2 rounds up the aggregated margin to the nearest 10,000
    Then Rounded aggregated market-risk-component margin remains 46,930,000 HKD
    And No change occurs as the value is already at the rounding boundary

  @data_validation @priority_high  # TC-SR-IMHK-3_2_5_1-01-data_validation-01
  Scenario: Validate all market risk components are present for aggregation
    Given A clearing participant has positions requiring margin calculation
    And Market risk components include Portfolio margin, Flat rate margin, Liquidation risk add-on, Structured product add-on, Corporate action position margin, and Holiday add-on
    When Step 1 calculates aggregated margin derived from market risk components
    Then All six market risk components are validated as present
    And Each component has a valid numeric value
    And Aggregation proceeds only when all components are available
