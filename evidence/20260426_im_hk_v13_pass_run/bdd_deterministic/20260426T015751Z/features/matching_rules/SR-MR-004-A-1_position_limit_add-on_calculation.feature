Feature: Position Limit Add-on Calculation
  SR-MR-004-A-1
  # paragraph_ids: MR-004-A-1
  Position Limit Add-on Calculation

  @positive @priority_high  # TC-SR-MR-004-A-1-positive-01
  Scenario: Calculate position limit add-on with standard portfolio inputs
    Given A CP portfolio with multiple instrument positions
    And Apportioned liquid capital of CP = 75,000,000
    And Apportioned liquid capital multiplier = 4
    And Apportioned liquid capital cap = 280,000,000
    And Add-on% = 25%
    And Portfolio margin components are available
    When The system calculates position limit add-on following Step 1 through Step 3
    Then Position limit add-on is calculated as 490,481 (rounded off to nearest integer)

  @boundary @priority_high  # TC-SR-MR-004-A-1-boundary-01
  Scenario: Position limit add-on returns zero when NMV equals zero
    Given A CP portfolio where net market value (NMV) equals zero
    And All other calculation parameters are valid
    When The system evaluates the position limit add-on formula
    Then Position limit add-on equals zero as per If(NMV = 0, 0, ...)

  @data_validation @priority_high  # TC-SR-MR-004-A-1-data_validation-01
  Scenario: Validate rounding to nearest integer for decimal result
    Given A CP portfolio with valid inputs producing decimal result
    And Rounding parameter is configured
    When The system applies rounding to the calculated position limit add-on
    Then Result is rounded off to nearest integer for decimal numbers
