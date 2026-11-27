Railway Safety Workflow Example
===============================

Introduction
============

This example illustrates how BASIL can be used to support a railway safety
assurance workflow and identify potential enhancement areas.

Example Scenario
================

A railway system shall prevent train overrun beyond the permitted movement
authority.

Hazard
======

HZ-001: Train fails to stop before the end of movement authority.

Safety Goal
===========

SG-001: Prevent train overrun through controlled braking intervention.

Safety Requirement
==================

SR-001: The onboard control system shall trigger emergency braking when the
calculated stopping distance exceeds the available movement authority.

Verification Activity
=====================

TC-001: Verify emergency braking activation when stopping distance calculations
indicate insufficient braking margin.

Evidence
========

TR-001: Emergency braking test execution report.

Additional evidence may include:

* Hazard analysis reports
* Safety assessments
* Independent reviews
* Checklists
* Certification records

Review and Approval
===================

* Reviewer: Safety Assessor
* Status: Approved
* Rationale: Requirement adequately mitigates identified hazard.

Traceability Relationships
==========================

::

   HZ-001
      |
      v
   SG-001
      |
      v
   SR-001
      |
      v
   TC-001
      |
      v
   TR-001
      |
      v
   Approval

Current BASIL Support
=====================

* Requirements management
* Test specifications and test cases
* Test execution and test results
* Reviews and comments
* Status and lifecycle management
* Traceability relationships

Potential Enhancements
======================

* Hazards as first-class work items
* Safety Goals as first-class work items
* Work items as traceability roots
* Support for non-test evidence artifacts
* Authority-based approval permissions
