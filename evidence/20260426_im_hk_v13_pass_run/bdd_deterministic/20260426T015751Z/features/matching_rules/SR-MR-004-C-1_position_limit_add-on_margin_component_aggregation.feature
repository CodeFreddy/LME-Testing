Feature: Position Limit Add-on Margin Component Aggregation
  SR-MR-004-C-1
  # paragraph_ids: MR-004-C-1
  Position Limit Add-on Margin Component Aggregation

  @positive @priority_high  # TC-SR-MR-004-C-1-positive-01
  Scenario: Calculate position limit add-on with aggregated margin components
    Given Portfolio margin = valid value
    And Flat rate margin = valid value
    And Corporate action position margin = valid value
    And Liquidation risk add-on = valid value
    And Structured product add-on = valid value
    And Rounding parameter = 10,000
    When The system aggregates and rounds up all margin components
    Then Aggregated margin is rounded up to nearest 10,000 parameter

  @boundary @priority_high  # TC-SR-MR-004-C-1-boundary-01
  Scenario: Add-on percentage application when net margin after credit equals zero
    Given Net margin after credit equals zero
    And Add-on% = 25%
    When The system evaluates If(Net margin after credit > 0, Add-on%, 1+ Add-on%)
    Then System applies (1 + Add-on%) = 125% as the multiplier

  @data_validation @priority_high  # TC-SR-MR-004-C-1-data_validation-01
  Scenario: Validate Add-on percentage parameter from circular notification
    Given HKSCC has issued circular notifying current Add-on%
    And System configuration reflects Add-on% = 25%
    When The system applies Add-on% in position limit add-on calculation
    Then Add-on% value matches the circular notification value
