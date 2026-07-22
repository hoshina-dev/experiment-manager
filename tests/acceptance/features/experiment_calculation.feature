@acceptance
Feature: Complete a ticketed lab experiment
  Ticketing Service can open an experiment and a lab worker can submit a
  measurement whose calculated result remains visible in the public API.

  Scenario: Calculate and persist a result for a ticket
    Given a ticket selects the current Proximate Analysis template for Coal
    When Ticketing Service creates the experiment
    Then the API returns the canonical experiment context
    When the lab worker submits a measurement value of 2.5
    And the lab worker requests the calculation
    Then the public experiment context reports a result of 250
