Railway Safety Workflow Example
===============================

Introduction
============

This example illustrates how BASIL can be used to support a railway
functional-safety workflow and identify potential enhancement areas.

The example is intentionally simple but demonstrates traceability across
multiple levels, from a system-level hazard down to ECU-level requirements,
verification activities, and supporting evidence.

System Context
==============

A railway system shall prevent train overrun beyond the permitted movement
authority.

The example focuses on the braking supervision function responsible for
ensuring safe train stopping behavior.

System Hazard
=============

HZ-001: Train fails to stop before the end of movement authority.

Potential consequences include:

* Collision
* Derailment
* Injury to passengers and personnel

Safety Goal
===========

SG-001: Prevent train overrun through controlled braking intervention.

Safety Function
===============

SF-001: Train Braking Supervision.

This function continuously monitors train speed, available movement authority,
and braking performance to determine whether emergency braking intervention is
required.

Electronic Control Unit
=======================

ECU-001: Braking Control Unit.

The Braking Control Unit implements braking supervision logic and contributes
to achievement of Safety Goal SG-001.

System Requirement
==================

SR-001: The onboard control system shall trigger emergency braking when the
calculated stopping distance exceeds the available movement authority.

ECU Requirement
===============

ECU-SR-001: The Braking Control Unit shall issue an emergency braking command
when braking-margin thresholds are exceeded.

Verification Activity
=====================

TC-001: Verify emergency braking activation when stopping-distance calculations
indicate insufficient braking margin.

Test Evidence
=============

TR-001: Emergency braking test execution report.

The test report demonstrates successful execution of the verification activity
and provides objective evidence that the braking function behaves as expected.

Non-Test Evidence
=================

SA-001: Braking Hazard Analysis Report.

This analysis demonstrates that emergency braking requirements contribute to
mitigation of Hazard HZ-001 and provides supporting safety evidence independent
of test execution results.

Additional examples of non-test evidence include:

* Safety assessments
* Independent reviews
* Checklists
* Certification records
* Safety case documents

Review and Approval
===================

The requirement, verification results, and supporting evidence are reviewed
before approval.

Example approval:

* Reviewer: Safety Assessor
* Status: Approved
* Rationale: Requirement adequately mitigates the identified hazard.

Traceability Relationships
==========================

Expected relationships are:

::

   System Hazard HZ-001
           |
           v
   Safety Goal SG-001
           |
           v
   Safety Function SF-001
           |
           v
   ECU Requirement ECU-SR-001
           |
           v
   Test Case TC-001
           |
           v
   Test Report TR-001
           |
           v
   Hazard Analysis SA-001
           |
           v
   Approval

Current BASIL Support
=====================

BASIL already provides:

* Requirements management
* Test specifications and test cases
* Test execution and test results
* Reviews and comments
* Status and lifecycle management
* Traceability relationships
* Export capabilities

Potential Enhancements
======================

This example highlights several potential areas for future enhancement:

* Hazards as first-class work items
* Safety Goals as first-class work items
* Safety Functions as first-class work items
* Work items as traceability roots
* Support for non-test evidence artifacts
* Evidence classification and typing
* Authority-based approval permissions
* Approval rationale capture

Relationship to Functional Safety Workflows
===========================================

Although this example is based on a railway scenario, similar concepts may
apply to other safety-critical domains including aerospace, automotive,
industrial automation, medical systems, and other functional-safety
environments.

The objective is to demonstrate how safety-related artifacts can be traced
through requirements, verification activities, evidence, reviews, and
approvals while identifying potential opportunities for future BASIL
enhancements.

The workflow may also serve as a basis for interoperability experiments and
exchange formats such as Safety Relevance Assertion Capability (SRAC). In
such scenarios, hazards, safety goals, requirements, evidence, reviews, and
approval relationships maintained within BASIL could be represented in an
external safety-context exchange format while preserving existing BASIL
traceability information.
