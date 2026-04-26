Feature: Favorable MTM Calculation and Margin Credit Application
  SR-MR-012-A-4
  # paragraph_ids: MR-012-A-4
  Favorable MTM Calculation and Margin Credit Application

  @positive @priority_high  # TC-SR-MR-012-A-4-positive-01
  Scenario: Favorable MTM calculated as Market value minus Contract value
    Given A portfolio with Market value of 700,000 and Contract value of 1,000,000
    When The favorable MTM is calculated
    Then The favorable MTM equals -700,000 (Market value - Contract value)

  @boundary @priority_high  # TC-SR-MR-012-A-4-boundary-01
  Scenario: Zero favorable MTM when Market value equals Contract value
    Given A portfolio where Market value equals Contract value
    When The favorable MTM is calculated
    Then The favorable MTM equals zero

  @data_validation @priority_high  # TC-SR-MR-012-A-4-data_validation-01
  Scenario: Negative MTM requirement absolute value added after margin credit
    Given A portfolio with a negative MTM requirement value
    When Margin credit is applied and the MTM requirement is processed
    Then The absolute value of the negative MTM requirement is added after margin credit application
