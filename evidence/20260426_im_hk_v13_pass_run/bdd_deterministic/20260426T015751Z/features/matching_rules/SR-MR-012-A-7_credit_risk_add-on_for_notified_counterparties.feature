Feature: Credit Risk Add-on for Notified Counterparties
  SR-MR-012-A-7
  # paragraph_ids: MR-012-A-7
  Credit Risk Add-on for Notified Counterparties

  @positive @priority_high  # TC-SR-MR-012-A-7-positive-01
  Scenario: Apply credit risk add-on to notified CP
    Given A Clearing Participant (CP) has been individually notified by HKSCC
    And The CP is flagged as eligible for credit risk add-on in the system
    When The initial margin calculation is performed for the notified CP
    Then The credit risk add-on is included in the margin calculation
    And The total margin reflects the credit risk add-on component

  @boundary @priority_high  # TC-SR-MR-012-A-7-boundary-01
  Scenario: CP at notification status boundary
    Given A CP has just received individual notification from HKSCC
    And The notification effective date is the current calculation date
    When The initial margin calculation is performed on the notification effective date
    Then The credit risk add-on is applied starting from the notification effective date
    And The margin calculation correctly reflects the new notification status

  @data_validation @priority_high  # TC-SR-MR-012-A-7-data_validation-01
  Scenario: Validate CP notification status for credit risk add-on
    Given A margin calculation request is submitted for a CP
    And The CP notification status is available in the system
    When The system determines whether to apply credit risk add-on
    Then The CP notification status is validated against HKSCC notification records
    And Credit risk add-on is applied only if the CP is confirmed as notified
    And An error is raised if notification status cannot be determined
