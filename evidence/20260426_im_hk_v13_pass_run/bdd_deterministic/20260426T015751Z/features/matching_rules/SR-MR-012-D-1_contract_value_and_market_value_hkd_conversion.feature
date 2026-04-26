Feature: Contract Value and Market Value HKD Conversion
  SR-MR-012-D-1
  # paragraph_ids: MR-012-D-1
  Contract Value and Market Value HKD Conversion

  @positive @priority_high  # TC-SR-MR-012-D-1-positive-01
  Scenario: Contract and market values converted to HKD equivalent
    Given A non-HKD denominated instrument position exists
    And Contract value in original currency is available
    And Market value in original currency is available
    When The system converts both contract value and market value to HKD equivalent
    Then Contract value in HKD equivalent is calculated
    And Market value in HKD equivalent is calculated
    And Both values use the same latest FX rate without haircut

  @boundary @priority_high  # TC-SR-MR-012-D-1-boundary-01
  Scenario: Conversion with minimum FX rate precision
    Given A non-HKD instrument position exists
    And FX rate has minimal decimal precision
    When The system applies the FX rate for conversion
    Then Conversion result maintains numeric precision
    And No haircut reduces the converted value
    And HKD equivalent values are rounded appropriately per position level

  @data_validation @priority_high  # TC-SR-MR-012-D-1-data_validation-01
  Scenario: Contract value and market value field validation
    Given A non-HKD instrument position exists in the Marginable Position Report
    When The system validates contract value and market value fields
    Then Contract value is a valid numeric value
    And Market value is a valid numeric value
    And Market value sign matches position quantity sign
    And Both fields are present for conversion
