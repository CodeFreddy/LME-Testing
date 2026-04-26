Feature: Position Limit Add-on NMV Calculation
  SR-MR-004-B-1
  # paragraph_ids: MR-004-B-1
  Position Limit Add-on NMV Calculation

  @positive @priority_high  # TC-SR-MR-004-B-1-positive-01
  Scenario: Calculate NMV with absolute value for net short position
    Given A CP portfolio with net short position (negative total market value)
    And Market values in HKD equivalent are available for all positions
    When The system calculates NMV by taking absolute value of net market value
    Then NMV equals absolute value of the negative portfolio market value

  @boundary @priority_high  # TC-SR-MR-004-B-1-boundary-01
  Scenario: NMV at apportioned liquid capital cap threshold
    Given NMV equals or exceeds 280,000,000 (apportioned liquid capital cap)
    And Apportioned liquid capital x multiplier = 300,000,000
    When The system applies Minimum[(Apportioned liquid capital x multiplier), cap] in formula
    Then Minimum function returns the cap value of 280,000,000

  @data_validation @priority_high  # TC-SR-MR-004-B-1-data_validation-01
  Scenario: Validate market value currency conversion to HKD equivalent
    Given Portfolio contains positions in multiple currencies
    And FX rates and haircut rates are available
    When The system sums market values in HKD equivalent for all positions
    Then All market values are converted to HKD equivalent before Step 1 summation
