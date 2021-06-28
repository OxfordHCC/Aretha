Tests in this directory are intended to test Aretha in an end to end
to end fashion. Usage of mocks is kept at a minimum, since we're
interested in how the software would perform in a real environment.

Somewhat related to behaviour driven testing, this type of testing is
only used to check whether the exposed interface fulfills reuirements
(whether functional or nonfunctional). We don't test implementations
here, but rather what the system is expected to do: the end
results. We treat Aretha as a black box, only interacting with it
through intended public interfaces and check whether the system is
changed based on scenarios.

These tests require a dedicated testing environment to be set-up and
thus will likely take longer to complete.
