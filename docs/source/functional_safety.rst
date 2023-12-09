.. image:: ../../app/src/app/bgimages/basil_black.svg

Functional Safety
=================




Most of the safety standards across different industry domains are based on requirements definition and associated verification and validation measures to bring the residual risk of failure down to an acceptable level (according to the target safety integrity level). When it comes to claim the systematic capability of SW elements, it is very important to trace requirements down to the specification of such SW elements and to respective tests at different levels (unit tests, integration tests, validation tests).

There are different reasons behind this:

1. Verification of completeness of safety activities: once we have full traceability in place from requirements to testing, it is much easier to detect if there is a gap between safety requirements, SW specifications and tests.
2. Assessment feasibility: with traceability in place it is easier to verify the correctness of tests against associated requirements and code specifications.
3. Maintainability of the safety case against incoming SW changes: if there are SW commits added later, with such traceability in place it is easier to determine the scope of requirements being impacted.
4. Scalability of the safety case: if there are requirements to be added / removed, with such traceability in place it is much easier to determine the impact on the rest of the safety case (i.e. which code and associated tests to be added or removed)

Complying to safety standards imply a great effort for quality departments.

Quality Engineers  have to produce different work items, like Software Requirements, Test Specifications, Test Cases, Test Reports and need to provide evidence and traceability for internal and/or external audits.

Usually that happens across a complex toolchain that involves several tools, and different file formats.

Having the data organized in a structured way helps to keep the situation under control and enables a proper data visualization for the most meaningful picture at any time.

BASIL provides a way to create quality related work items and to relate them to a snippet of the specification document or to a snippet of the source code creating a view that will help you keep track of the status of the analysis.


Read the `full article <https://elisa.tech/blog/2023/11/30/basil-the-fusa-spice/>`_ at `elisa.tech <https://elisa.tech/blog/2023/11/30/basil-the-fusa-spice/>`_


.. toctree::
   :maxdepth: 1
   :caption: Contents:
