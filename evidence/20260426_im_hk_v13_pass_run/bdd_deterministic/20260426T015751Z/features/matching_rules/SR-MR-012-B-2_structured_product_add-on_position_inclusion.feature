Feature: Structured Product Add-on Position Inclusion
  SR-MR-012-B-2
  # paragraph_ids: MR-012-B-2
  Structured Product Add-on Position Inclusion

  @positive @priority_high  # TC-SR-MR-012-B-2-positive-01
  Scenario: Long position instrument included in structured product add-on
    Given An instrument is identified under FieldType 6
    And The instrument has a positive quantity (e.g., 110,000,000)
    When The system determines position classification for structured product add-on
    Then The instrument is classified as long position
    And The instrument is included in structured product add-on calculation
    And Structured product add-on is calculated using Quantity x Tick size multiplier x Minimum tick size

  @boundary @priority_high  # TC-SR-MR-012-B-2-boundary-01
  Scenario: Quantity boundary for position classification
    Given An instrument is identified under FieldType 6
    And The instrument quantity is at the boundary value (e.g., quantity = 1 or quantity approaching zero from positive side)
    When The system determines whether to include the instrument in structured product add-on
    Then Quantity greater than zero results in long position classification
    And Long position instruments are included in structured product add-on
    And Quantity equal to zero or negative results in exclusion from calculation

  @data_validation @priority_high  # TC-SR-MR-012-B-2-data_validation-01
  Scenario: Quantity field validation for position classification
    Given An instrument position exists in the Marginable Position Report
    When The system validates and interprets the quantity field
    Then Quantity is a valid numeric value
    And Positive quantity is correctly identified as long position
    And Negative quantity is correctly identified as short position
    And Position classification determines inclusion/exclusion in structured product add-on
