Feature: Risk Parameters and Margin Adjustments Input Sources
  SR-MR-003-B6-1
  # paragraph_ids: MR-003-B6-1
  Risk Parameters and Margin Adjustments Input Sources

  @positive @priority_high  # TC-SR-MR-003-B6-1-positive-01
  Scenario: Apply risk parameters from IMRPF source for margin calculation
    Given IMRPF source provides risk parameters
    And Market risk component data is available
    And Position details are complete with all required fields
    When The calculation applies risk parameters from IMRPF to derive total MTM and margin requirement
    Then Market risk component is included in calculation
    And Portfolio margin is applied
    And Flat rate margin is applied
    And Total MTM and margin requirement is calculated

  @boundary @priority_high  # TC-SR-MR-003-B6-1-boundary-01
  Scenario: Calculate margin with minimum contract value threshold
    Given Risk parameters are available from IMRPF
    And Position has valid InstrumentID and Quantity
    And Contract value is at minimum non-zero threshold
    When The calculation of total MTM and margin requirement is executed
    Then Calculation completes successfully
    And Margin requirement reflects minimum contract value contribution

  @data_validation @priority_high  # TC-SR-MR-003-B6-1-data_validation-01
  Scenario: Validate HKD equivalent conversion for contract and market values
    Given Position data includes Contract value and Market value fields
    And Values may be in non-HKD currencies requiring conversion
    When Contract value and Market value are validated for HKD equivalent format
    Then Contract value is validated as HKD equivalent
    And Market value is validated as HKD equivalent
    And Currency conversion is applied if original values are in different currency
