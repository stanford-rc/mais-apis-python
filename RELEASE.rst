Release Process
===============

This document explains how to do a release!

We use the following branch/tag layout:

* Every release has a tag, whose name matches the form ``vX.Y.Z``.
  For example, the source for version 1.5.0 is available via the tag
  ``v1.5.0``.
  The tag's message includes the changelog of items included in this release.

* Every supported combination of major/minor version has a branch, whose name
  matches the form ``vX.Y``.  For example, all releases from 0.50 up to (but
  not including) 0.51 may be found in the ``v0.50`` branch.

* The ``main`` branch contains the code that will become the next major/minor
  release.  For example, if the latest release is 1.10.3, the ``main`` branch
  will contain the code that will eventually become either version 2.0.0 or
  version 1.11.0.

Making a new release involves creating a new tag, and (when making a new
major or minor release) creating a new branch.

The GitHub Actions workflow should do all the work of uploading to PyPi:
Commits (including those creating new branches) trigger a publish to Test PyPi;
tags trigger a publish to production PyPi.

Prerequisites
-------------

Before doing a release, you should check the following things:

* **The last commit must pass all Actions.**  Check the most-recent commit on
  the branch from which you are creating the release: All GitHub Actions must
  have passed successfully.

  If anything failed, push additional commits as needed to get things passing.
  If there is a transient issue (like an issue with the GitHub Actions
  service), wait until all transient issues have passed.

* **The VERSION number must be correct.**  The ``VERSION`` file contains the
  version number of the *next* release.  What this means depends on if you are
  in the ``main`` branch, or in a minor-version branch.

  For example, suppose the latest release is 1.5.0, and the latest 1.4.x
  version is 1.4.2.  In that case…

  * The VERSION file in the main branch should be set to either ``1.6.0`` or
    (if the decision has been made to make a major release) ``2.0.0``.

  * The VERSION file in the ``v1.4`` branch should be set to ``1.4.3``.

  If the VERSION file is not correct, make a commit to fix it.

* **You have access to PyPi.**  On Test PyPi, you will be cleaning up old dev
  releases.  And in case something goes wrong, you might be yanking or deleting
  releases from either Test PyPi or production PyPi.

  So, before doing a release, make sure you can log in to Test PyPi *and*
  production PyPi.

Process
-------

Ready to do a release?  Here are the instructions!

**STEP 0: Check prerequisites**

Check that all of the prerequisites are met.  If not, do what you need to do
for them to be met.

**STEP 1: Clean up old 'dev' releases**

Every time a push is made to the repository, a release is made on Test PyPi.
The script ``update-version-for-test-push.py`` is used to increment the version
number (in the ``VERSION`` file) for the developmental release to Test PyPi.

.. note::
   The ``update-version-for-test-push.py`` script runs inside the GitHub
   Actions worker.  It does not make any changes to the repository.

For per-commit releases to Test PyPi, the version number used is a
`developmental release`_ version.  Per the Python Packaging `Version
specifiers`_ page, a developmental release sorts before the actual release.
So, if the ``VERSION`` file says the next release is 1.2.3, the script will
change the version to ``1.2.3devYYYYMMDDHHMMSS``, using the release datetime.
Per Python's rules for version-number sorting, this development release version
will sort *before* version 1.2.3.

.. _developmental release: https://packaging.python.org/en/latest/specifications/version-specifiers/#developmental-releases
.. _Version specifiers: https://packaging.python.org/en/latest/specifications/version-specifiers/

Since every push triggers an upload to Test PyPi, a lot of developmental
releases can build up.  When it is time to make a new release, you should
delete (not yank, delete) all but the most recent few developmental releases.

.. danger::
   Do not delete releases from PyPi without an *extremely* good reason!

**STEP 1: Switch branches**

Switch to the branch containing the code you are releasing.  If you are
releasing a patch, then you should be on the appropriate ``vX.Y`` branch.  If
you are releasing a new major or minor version, then you should be on the
``main`` branch.

**STEP 2: Update & commit Changelog for release**

Update the ``CHANGELOG.rst`` file for the release.  This involves making two
changes to the file:

1. Change ``Unreleased`` to the version number of the next release (from the
   ``VERSION`` file).  Extend or reduce the length of the ``-------``
   separateor line as appropriate.

2. Remove all empty sections.  For example, if this release did not have any
   enhancements, remove the "Enhancements:" text, and its associated blank
   lines.

When committing the change, use a commit message similar to "CHANGELOG: Update
for release X.Y.Z".

Push your commit.  Wait for the commit to successfully pass the GitHub Actions
workflow.

.. warning::
   If the GitHub Actions workflow fails, diagnose and fix the error.  Do not
   continue until the GitHub Actions workflow succeeds.

**STEP 3: Tag release**

Make an annotated tag of the commit you just pushed.  The tag's name will be
the lowercase letter 'v' followed by the version number.  For example, version
1.2.2 would be tagged ``v1.2.2``, and version 2.0.0 would be tagged ``v2.0.0``.

.. note::
   All releases have three components to the version number.  For example,
   "2.2.0" is a valid version; "2.2" is not.

For the tag message, use the contents of the ``CHANGELOG.rst`` file for this
release.  Copy the text verbatim, starting with the release number, then remove
the separator line.

For example, if your changelog for this release looks like this::

    1.22.0
    ------

    Enhancements:

    * Stuff!

    Fixes:

    * Other stuff

… then the tag message will look like this::

    1.22.0

    Enhancements:

    * Stuff!

    Fixes:

    * Other stuff

Do one last check that the version in the tag name matches contents of the
``VERSION`` file, then push the tag.

This will trigger a GitHub Actions run that will include a publish to
production PyPy.  Wait for this to complete.

**STEP 4: For major/minor releases, make a new branch**

.. note::
   If you released a patch version (for example, 1.2.1), skip this step.

If you have just released a new major or minor release, make a branch for the
release.  The branch's name will be the lowercase letter 'v' followed by the
major and minor version.  **Do not include the patch number in the branch
name!**

For example, if you just released version 2.0.0, the branch name would be
``v2.0``; if you just released version 1.2.0, the branch name would be
``v1.2``.

Switch to this new branch, but *do not push the branch yet*.  You will push the
new branch in the next step.

**STEP 5: Increment version & add a new Changelog**

In the branch, as two spearate commits, increment the version number and
prepare the changelog for future changes.

To change the ``VERSION`` file, take the existing version number and increment
the patch component.  For example, if you just released version 0.48.0, change
the ``VERSION`` file to ``0.48.1``.  If you just released version 1.22.1,
change the ``VERSION`` file to ``1.22.2``.  Make a commit, with the message
"VERSION: Incrementing for future release".

Next, update the ``CHANGELOG.rst`` file, making space for unreleased changelog
entries.  To do this, add the following text to the top of the file::

    Unreleased
    ----------

    Enhancements:


    Fixes:


    Other:


    … existing changelog begins here …

Make a commit, with the message "CHANGELOG: Make space for future changes".

Push the changes to GitHub.  If you made a new branch in Step 4, this will also
create the new branch on GitHub.

The push will trigger a new round of GitHub Actions workflow, including a
publish to Test PyPi.  Wait for that push to complete, then confirm the publish
has the correct pre-release version number.

**STEP 6: For major/minor releases, update main**

.. note::
   If you released a patch version (for example, 1.2.1), skip this step.

If you just made a major or minor release, switch back to the ``main`` branch.

Once you are back on the ``main`` branch, make two commits:

1. Update the ``VERSION`` file for a future major or minor release.  For
   example, if you just released version 1.2.0,  the ``VERSION`` file should be
   changed to either ``1.3.0`` or ``2.0.0``.

2. Update the ``CHANGELOG.rst`` file, making space for unreleased changelog
   entries.  Use the template from Step 5.

Push your two ``main``-branch commits to GitHub.

The push will trigger a new round of GitHub Actions workflow, including a
publish to Test PyPi.  Wait for that push to complete, then confirm the publish
has the correct pre-release version number.

**Release complete!**

Congratulations, you have made a release!

Old-Version Cleanup
-------------------

We should **never** delete tags from GitHub, nor should we ever delete
releases from production PyPi.

.. note::
   PyPi has a 10 GiB storage quota for each project.  With releases taking
   under 100 kiB per release, it will be a long time before we reach that
   quota.

Instead, from time to time, we should clean up the following:

* **Test PyPi pre-releases**, as documented in Step 1 of the release process.

* **Old branches.**

We should only maintain branches for releases that we plan on keeping
up-to-date.  In other words, if you have a branch for a release, that is a sign
to clients that they can continue expecting bugs to be patched.

Besides the ``main`` branch, it is appropriate to keep one or two minor-release
branches around.  `Semantic Versioning`_ dictates that breaking changes require
a new major version, so it is reasonable to expect clients will likely be
staying on a minor version for some time.

.. _Semantic Versioning: https://semver.org

There is no special process for cleaning up old branches.  Simply use your
normal Git tools to delete a branch, and to push the branch deletion to GitHub.

.. note::
   Git normally complains if you delete a branch containing un-merged changes.
   You should expect to see this warning, because the tip of every branch
   includes commits to increment the ``VERSION`` file, and to add blank spaces
   to the ``CHANGELOG.rst`` file.

   Those commits are made at the end of the release process; if a branch will
   stop receiving updates, it is OK to abandon those commits.
