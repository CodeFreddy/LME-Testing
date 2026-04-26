Feature: Contract Value Preservation During Corporate Action Adjustment
  SR-MR-004-E-3
  # paragraph_ids: MR-004-E-3
  Contract Value Preservation During Corporate Action Adjustment

  @positive @priority_high  # TC-SR-MR-004-E-3-positive-01
  Scenario: Contract value remains unchanged after corporate action adjustment
    Given A clearing participant holds a position with instrument code 5
    And Trade date is 04/11/2019 with quantity 400 and contract value 24,000
    And A bonus share/stock split corporate action exists with quantity conversion ratio of 2
    When The system performs corporate action position adjustment
    And Position quantity is adjusted by multiplying original quantity by conversion ratio
    Then The new position quantity equals 800 (400 x 2)
    And The contract value remains unchanged at 24,000
    And Only the quantity field is modified, contract value is preserved

  @negative @priority_high  # TC-SR-MR-004-E-3-negative-01
  Scenario: Contract value modification during adjustment is rejected
    Given A clearing participant holds a position with a defined contract value
    And A corporate action requiring position adjustment is being processed
    And The adjustment process attempts to modify the contract value
    When The system processes the corporate action adjustment
    And An invalid operation attempts to change the contract value
    Then The contract value modification is rejected
    And The original contract value is preserved
    And Only position quantity is adjusted according to the conversion ratio

  @data_validation @priority_high  # TC-SR-MR-004-E-3-data_validation-01
  Scenario: Validate contract value field integrity during adjustment
    Given A position exists with instrument code, quantity, and contract value
    And Corporate action position adjustment is being performed
    When The system validates the contract value field
    And Pre-adjustment contract value is recorded
    And Post-adjustment contract value is compared
    Then Contract value before adjustment equals contract value after adjustment
    And Data integrity check passes
    And Adjustment is marked as valid
