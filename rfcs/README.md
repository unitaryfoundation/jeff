# Jeff RFCs
[Jeff RFCs]: #jeff-rfcs

The "RFC" (request for comments) process is intended to provide a consistent
and controlled path for changes to Jeff (such as new features) so that all
stakeholders can be confident about the direction of the project.

Many changes, including bug fixes and documentation improvements can be
implemented and reviewed via the normal GitHub pull request workflow.

Some changes though are "substantial", and we ask that these be put through a
bit of a design process and produce a consensus among the community and maintainers.

## Table of Contents
[Table of Contents]: #table-of-contents

  - [Opening](#jeff-rfcs)
  - [Table of Contents]
  - [When you need to follow this process]
  - [Before creating an RFC]
  - [What the process is]
  - [Implementing an RFC]
  - [Help this is all too informal!]
  - [License]


## When you need to follow this process
[When you need to follow this process]: #when-you-need-to-follow-this-process

You need to follow this process if you intend to make "substantial" changes to
the Jeff format, the project, or the RFC process itself. What constitutes a
"substantial" change is evolving based on community norms and varies depending
on what part of the ecosystem you are proposing to change, but may include the
following.

  - Any change to the Jeff specification that is not a bugfix or documentation improvement.
  - Large reorganizations of the Jeff project.
  - New sub-project or package initiatives.

Some changes do not require an RFC:

  - Rephrasing, reorganizing, refactoring, or otherwise "changing shape does
    not change meaning".


## Before creating an RFC
[Before creating an RFC]: #before-creating-an-rfc

A hastily-proposed RFC can hurt its chances of acceptance. Low quality
proposals, proposals for previously-rejected features, or those that don't fit
into the near-term roadmap, may be quickly rejected, which can be demotivating
for the unprepared contributor. Laying some groundwork ahead of the RFC can
make the process smoother.

Although there is no single way to prepare for submitting an RFC, it is
generally a good idea to pursue feedback from other project developers
beforehand, to ascertain that the RFC may be desirable; having a consistent
impact on the project requires concerted effort toward consensus-building.


## What the process is
[What the process is]: #what-the-process-is

In short, to get a major feature added to Jeff, one must first get the RFC
document merged into the repository as a markdown file. At that point the RFC is
"active" and may be implemented with the goal of eventual inclusion into Jeff.

  - Fork the Jeff repo [Jeff repository]
  - Copy `rfcs/0000-template.md` to `rfcs/text/0000-my-feature.md` (where "my-feature" is
    descriptive). Don't assign an RFC number yet; This is going to be the PR
    number and we'll rename the file accordingly if the RFC is accepted.
  - Fill in the RFC. Put care into the details: RFCs that do not present
    convincing motivation, demonstrate lack of understanding of the design's
    impact, or are disingenuous about the drawbacks or alternatives tend to
    be poorly-received.
  - Submit a pull request. As a pull request the RFC will receive design
    feedback from the larger community, and the author should be prepared to
    revise it in response.
  - Now that your RFC has an open pull request, use the issue number of the PR
    to rename the file: update your `0000-` prefix to that number. Also
    update the "RFC PR" link at the top of the file.
  - Build consensus and integrate feedback. RFCs that have broad support are
    much more likely to make progress than those that don't receive any
    comments. Feel free to reach out to the RFC assignee in particular to get
    help identifying stakeholders and obstacles.
  - The maintainers will discuss the RFC pull request, as much as possible in the
    comment thread of the pull request itself. Offline discussion will be
    summarized on the pull request comment thread.
  - RFCs rarely go through this process unchanged, especially as alternatives
    and drawbacks are shown. You can make edits, big and small, to the RFC to
    clarify or change the design, but make changes as new commits to the pull
    request, and leave a comment on the pull request explaining your changes.
    **Specifically, do not squash or rebase commits after they are visible on
    the pull request.**
  - If the RFC requires an implementation, a new issue should be created in the [Jeff repository] and linked to the RFC document.
  - At some point, once the community has reached a consensus, the RFC will be
    either merged or closed. This should be done with enough notice that all
    stakeholders have a chance to lodge any final objections before a decision
    is reached.


## Implementing an RFC
[Implementing an RFC]: #implementing-an-rfc

If the RFC requires changes to be made in the repository, an associated issue
for the RFC's implementation will be created in the [Jeff repository].

The author of an RFC is not obligated to implement it. Of course, the RFC
author (like any other developer) is welcome to post an implementation for
review after the RFC has been accepted.



### Help this is all too informal!
[Help this is all too informal!]: #help-this-is-all-too-informal

The process is intended to be as lightweight as reasonable for the present
circumstances. As usual, we are trying to let the process be driven by
consensus and community norms, not impose more structure than necessary.


## License
[License]: #license

RFC proposals are licensed under the Apache License, Version 2.0.

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in the work by you, as defined in the Apache-2.0 license, shall be licensed under the same license.


[Jeff repository]: https://github.com/unitaryfoundation/jeff
