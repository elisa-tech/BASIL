# <img src="app/src/app/bgimages/basil_black.svg" alt= "BASIL | The FuSa Spice" height="85">

# BASIL

A tool developed to manage software related work items, design their traceability towards specifications and ensure completeness of analysis.

It comes with a web user interface to provide a simplified view of work item relationships and with a REST web api to simplify the integration in other toolchains.

## What is it for?

With BASIL you can decompose a Software Component Specification (or source code directly) in snippets and assign to each one a set of desired work items.

BASIL will help you on identifying gaps and on tracking progress.

## Supported Work Items

- Software Requirements
- Test Specifications
- Test Cases
- Test Runs
- Test Run Configurations
- Justifications
- Documents

## Test Infrastructure

BASIL comes with its own test infrastructure that allow users to run any kind of test case (written in any programming language)
against different kind of test environment, such as containers, virtual machines, physical hardwares.
That is possible thanks to a Test Management Tool (**tmt**), a python project that is using metadata files (**fmf** format) to describe test cases, test plans and user stories.
The metadata file is the abstraction layer BASIL needs to run any kind of test case.
**tmt** is also able to provision different kind of test environment, as the one above listed.

## Trace test executed on external infrastructures

BASIL is also able to trace test cases executed on external test infrastructure such as

- KernelCI
- Testing Farm
- github actions
- gitlab CI

to test cases.

## How to run it

BASIL consists of 2 sub projects, follow links for further details:

- api - [README](api/README.md)
- app - [README](app/README.md)

Moreover you need to init a database to be able to use BASIL:

- db - [README](db/README.md)

## Documentation

BASIL The FuSa Spice documentation is available [here](https://basil-the-fusa-spice.readthedocs.io/)

## Links

- [ELISA BASIL Instance](http://elisa-builder-00.iol.unh.edu:9056/)
- [ELISA Webinar: Introducing Basil](https://elisa.tech/blog/2023/10/04/introducing-basil-video/)
- [Critical Software Summit - OSS North America Seattle 2024](https://www.youtube.com/watch?v=1xmcpco14nE)
- [Critical Software Summit - OSS Europe Wien 2024](https://www.youtube.com/watch?v=dTXGpzM6eYw&pp=ygUVc3VtbWl0IHNvZnR3YXJlIGJhc2ls)
- [Linux Plumbers - Wien 2024](https://www.youtube.com/watch?v=3QuEXTafxT0&pp=ygUZbGludXggcGx1bWJlcnMgMjAyNCBiYXNpbA%3D%3D)
- [Youtube - BASIL The Fusa Spice](https://www.youtube.com/@basil-the-fusa-spice/videos)
- [ELISA Blog](https://elisa.tech/blog/)
- [tmt - github](https://github.com/teemtee/tmt)
- [tmt - documentation](https://tmt.readthedocs.io/en/stable/)
