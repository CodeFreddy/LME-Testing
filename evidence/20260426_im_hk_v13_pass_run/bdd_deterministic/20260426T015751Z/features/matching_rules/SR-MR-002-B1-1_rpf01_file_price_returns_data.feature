Feature: RPF01 File Price Returns Data
  SR-MR-002-B1-1
  # paragraph_ids: MR-002-B1-1
  RPF01 File Price Returns Data

  @positive @priority_high  # TC-SR-MR-002-B1-1-positive-01
  Scenario: RPF01 file includes all required price return scenarios
    Given RPF01 file is generated for the current business day
    When the file is processed to extract price return data
    Then instrument price returns for historical Value-at-Risk (HVaR) scenarios are included
    And instrument price returns for stress Value-at-Risk (SVaR) scenarios are included
    And flat rate margin scenarios are included
    And beta hedge information for liquidation risk add-on is included

  @negative @priority_high  # TC-SR-MR-002-B1-1-negative-01
  Scenario: RPF01 file missing required price return scenarios
    Given RPF01 file is generated with incomplete price return data
    And one or more required scenario types are missing
    When the file is processed for margin calculation
    Then the system detects missing required price return scenarios
    And appropriate error or warning is raised for the incomplete file

  @data_validation @priority_high  # TC-SR-MR-002-B1-1-data_validation-01
  Scenario: Validate RPF01 file data structure and format
    Given RPF01 file is received for processing
    When the system validates the file layout and data structure
    Then price threshold data is present and valid
    And add-on% for structured product add-on is present and valid
    And corporate action position margin scenarios data is present and valid
