Feature: Position Limit Add-on Calculation
  SR-MR-004-D-1
  # paragraph_ids: MR-004-D-1
  Position Limit Add-on Calculation

  @positive @priority_high  # TC-SR-MR-004-D-1-positive-01
  Scenario: Calculate position limit add-on with valid portfolio inputs
    Given A clearing participant has a portfolio with multiple positions
    And Apportioned liquid capital of CP is 75,000,000
    And Apportioned liquid capital multiplier is 4
    And Apportioned liquid capital cap is 280,000,000
    And Net margin after credit is 41,930,000
    And Add-on% is 25%
    And Total market values in HKD equivalent sum to 300,700,000
    When The system calculates the position limit add-on using the formula
    And NMV = Absolute value of portfolio net market value
    And Position limit add-on = Maximum {NMV – Minimum [(Apportioned liquid capital x multiplier), cap], 0} / NMV x Round up(aggregated margin, 10,000) x Add-on%
    Then NMV is calculated as 300,700,000
    And Position limit add-on equals 490,481 (rounded to nearest integer)

  @boundary @priority_high  # TC-SR-MR-004-D-1-boundary-01
  Scenario: Position limit add-on when NMV equals zero
    Given A clearing participant has a portfolio
    And The sum of market values in HKD equivalent results in net market value of zero
    And All positions net out to zero total market value
    When The system calculates the position limit add-on
    And NMV = 0 is detected
    Then Position limit add-on equals 0
    And The formula returns zero immediately without further calculation

  @data_validation @priority_high  # TC-SR-MR-004-D-1-data_validation-01
  Scenario: Validate required input data for position limit add-on calculation
    Given A clearing participant portfolio exists
    And The system is ready to calculate position limit add-on
    When Input data is validated for
    And Apportioned liquid capital value
    And Apportioned liquid capital multiplier
    And Apportioned liquid capital cap
    And Net margin after credit
    And Add-on% percentage
    And Market values in HKD equivalent for all positions
    Then All required numeric fields are present and valid
    And Market values are converted to HKD equivalent
    And Calculation proceeds only when all validations pass
