Feature: Intra-day MTM Requirement Calculation
  SR-MR-004-B1-1
  # paragraph_ids: MR-004-B1-1
  Intra-day MTM Requirement Calculation

  @positive @priority_high  # TC-SR-MR-004-B1-1-positive-01
  Scenario: Successful Intra-day MTM Requirement Calculation
    Given Valid position data and price inputs are available for the trading day
    When Intra-day MTM Requirement Calculation is triggered
    Then MTM Requirement is calculated and returned successfully

  @boundary @priority_high  # TC-SR-MR-004-B1-1-boundary-01
  Scenario: Intra-day MTM Requirement Calculation at 11:00 a.m. HKT boundary
    Given Position data is available before the scheduled calculation time
    When Intra-day MTM Requirement Calculation is triggered at 11:00 a.m. HKT
    Then MTM Requirement calculation is accepted and processed at the specified time

  @data_validation @priority_high  # TC-SR-MR-004-B1-1-data_validation-01
  Scenario: Currency data validation for Cross-currency Netting on MTM Requirement
    Given Position data with currency information is submitted for MTM calculation
    When Cross-currency Netting on MTM Requirement is processed
    Then Currency data is validated and calculation proceeds with valid currency inputs
