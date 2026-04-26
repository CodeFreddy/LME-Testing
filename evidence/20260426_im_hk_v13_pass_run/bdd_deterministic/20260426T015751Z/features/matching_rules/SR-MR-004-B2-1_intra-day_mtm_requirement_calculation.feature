Feature: Intra-day MTM Requirement Calculation
  SR-MR-004-B2-1
  # paragraph_ids: MR-004-B2-1
  Intra-day MTM Requirement Calculation

  @positive @priority_high  # TC-SR-MR-004-B2-1-positive-01
  Scenario: Successful Cross-day Position Netting Calculation
    Given Valid position data spanning multiple trading days is available
    When Cross-day Position Netting calculation is triggered
    Then Position netting result is calculated and returned successfully

  @boundary @priority_high  # TC-SR-MR-004-B2-1-boundary-01
  Scenario: Intra-day MTM Requirement Calculation at 2:00 p.m. HKT boundary
    Given Position data is available before the scheduled calculation time
    When Intra-day MTM Requirement Calculation is triggered at 2:00 p.m. HKT
    Then MTM Requirement calculation is accepted and processed at the specified time

  @data_validation @priority_high  # TC-SR-MR-004-B2-1-data_validation-01
  Scenario: Currency data validation for Position Limit Add-on Calculation
    Given Position data with currency information is submitted for Position Limit Add-on calculation
    When Detailed Calculation on Position Limit Add-on is processed
    Then Currency data is validated and calculation proceeds with valid currency inputs
