## Same load, same versions: minimal version selection for Metacello
@chamvs

This chapter is an edited transcript of a presentation given by Guille Polito on November 17, 2026, and of the discussion that took place during the talk. The spoken text has been reorganized and turned into prose, the code and the reports come from the slides and from the live demos, and the version trees have been redrawn.

The chapter presents _minimal version selection_ (MVS), an algorithm that chooses which version of each project to load, and how it was integrated into Metacello, the project loader of Pharo. It starts with the problems of the current Metacello, describes the algorithm step by step on one example, and then shows the pieces needed to make it work in Pharo: a resolution step, reading baselines without loading them, taking the image into account, cleaning up, reporting problems, and working on branches.

!!note At the time of the talk the implementation was recent. It was written mostly by Claude, by alternating design discussions, implementation and code review. In the week before the talk the practice became stricter: every line is reviewed, and what is not accepted is either fixed or logged in a backlog.

### The problem: which version do we load?
@secproblem

Consider a project `A` that depends on `B`. `B` depends on `C` and on `D`, and `D` depends on `C` too. You can read it with real projects: Toplo depends on Bloc, which has several dependencies, and some of them share a dependency. Figure *@figdiamond@* shows the situation: `B` asks for `C 1.2` and `D` asks for `C 1.3`. Which version of `C` should be loaded?

![Two baselines ask for two versions of the same project.](figures/diamond.png width=60&label=figdiamond)

With the current Metacello the answer depends:
- on the order in which Metacello walks the baselines,
- on what is already loaded in the image,
- on what was released yesterday, when a baseline points to a branch: `master` today is not `master` tomorrow.

The same load can give different versions.

#### Conflicts are decided in the middle of the load

Metacello walks the baselines, and when it finds a conflict it signals an exception. The default action of this exception opens a popup. A load script can install handlers to avoid the popup:

```language=pharo
Metacello new
	baseline: 'A';
	repository: 'github://me/A:v1.0';
	onConflict: [ :ex | ex useIncoming ];
	onUpgrade: [ :ex | ex useLoaded ];
	load
```

Written this way, a handler decides all the conflicts in the same manner: the script above uses the incoming version for all the conflicts and the loaded one for all the upgrades. It is possible to do better by testing which project the exception is about. It is harder, and in practice nobody does it.

#### It fails late and does not say why

Because decisions are taken while baselines are being loaded, a problem may appear when the load is half done. Something may stay half loaded, checked out and dirty. In addition, the loader does not say who asked for what, nor what you could do about it.

#### Projects cannot be developed together

The developers of Toplo want to develop Toplo and Bloc at the same time, each one on its own branch, and to test them together in the CI. There is no way to express it today without editing baselines. A developer who works with baselines pointing to branches has to change them to point to tags before each release, and to put the branches back just after the release. This is a lot of noise.

#### Reproducible first

These needs pull in opposite directions. One or two people develop Bloc while many more want to use it. The goal is to help the team develop, but first to help the many users. Therefore the loader should be _reproducible first_, and not branch first. The question that drives the rest of the chapter is the following one:

_What if the same load always chose the same versions, before touching the image?_

This has a cost. When a baseline points to a branch, you always get the latest version of everything: you are never reproducible and always on the bleeding edge. Here it is the other way around. By default nothing is upgraded, you always get the same versions, and an upgrade has to be asked for explicitly. It also raises a list of questions that we will answer one by one:

- _Upgrades._ `C 1.4` is out with a fix. Who gets it?
- _The image._ `F 4.2` is already installed. What happens to it?
- _Branches._ I want `C` from `main`. How do I say it?
- _Conflicts._ `B` asks for `C 1.2` and `D` asks for `C 2.0`. What can be done?
- _Old code._ Someone asks for `C 1.0`, which no longer compiles. What do we do?

### Minimal version selection
@secmvs

Minimal version selection comes from Go. It was proposed by Russ Cox in 2018, in the _vgo_ proposal ([https://research.swtch.com/vgo-mvs](https://research.swtch.com/vgo-mvs)). It is part of Go modules since Go 1.11 (2018), it is the default since Go 1.16 (2021), and it is still the way Go chooses versions. Go chose it because it is:

- _reproducible_: builds can be reproduced without a lock file listing exactly what was built,
- _predictable_: a new release changes nothing,
- _simple and fast_: there is no SAT solver, only a small algorithm with a worklist.

#### The rule

The rule has three parts:

- each baseline asks for a _minimum_ version of each of its dependencies,
- for each project, MVS keeps the _highest minimum_ that was asked,
- this is the _lowest_ version that satisfies everybody.

In the example of Figure *@figdiamond@*, `C 1.2` and `C 1.3` are compatible because they have the same major version. MVS takes the highest of the two, `C 1.3`. If there is a newer release `C 1.4`, it is not in the dependency tree and it is not loaded.

#### MVS step by step

Let us extend the example. `C 1.2` depends on `E 3.5`, while `C 1.3` depends on `F 4.2`. The algorithm follows the dependencies declared in the baselines and maintains the list of selected versions. In the figures, orange marks what the current step adds or changes, and a dashed node is a version that was asked for and then superseded.

We start from `A 1.0`, the root of the load. `A` asks for `B 1.0` (Figure *@figstep1@*).

![`A` asks for `B 1.0`.](figures/step1.png width=45&label=figstep1)

`B 1.0` asks for `C 1.2` and `D 2.1`. Both are added to the list (Figure *@figstep2@*).

![`B` asks for `C 1.2` and `D 2.1`.](figures/step2.png width=58&label=figstep2)

We look at the dependencies of `C 1.2`: it asks for `E 3.5` (Figure *@figstep3@*).

![`C 1.2` asks for `E 3.5`.](figures/step3.png width=72&label=figstep3)

Then `D 2.1` asks for `C 1.3`. A version of `C` is already selected. Since `1.3` is higher than `1.2` and compatible with it, `C` goes up from `1.2` to `1.3` (Figure *@figstep4@*).

![`D` asks for `C 1.3`: `C` goes up from 1.2 to 1.3.](figures/step4.png width=72&label=figstep4)

Finally we look at the dependencies of `C 1.3`: it asks for `F 4.2` (Figure *@figstep5@*).

![`C 1.3` asks for `F 4.2`.](figures/step5.png width=85&label=figstep5)

Each requested version is visited once, and each time a request is found the list is updated if needed. The result, called the _build list_, gives one version per project: `A 1.0`, `B 1.0`, `C 1.3`, `D 2.1`, `E 3.5` and `F 4.2`.

#### A new release changes nothing

Figure *@figreleased@* compares the versions that exist with the versions that were selected. `C 1.4`, `D 2.2` and `E 3.6` exist, but no baseline asks for them, so they are not taken into account.

![Released versions, asked versions and selected versions.](figures/released.png width=45&label=figreleased)

Two properties follow:

- A new release changes nothing until a baseline asks for it. A developer can release without disturbing others: it only has an effect on those who ask for the new version explicitly.
- Requirements are never removed during the walk, so the order of the walk does not matter.

For Toplo and Bloc this matters because the dependency graph is not a tree. Both Toplo and Album depend on Bloc. With the current Metacello, when they do not ask for the same version of Bloc, a popup opens. With MVS, the right version is selected automatically, it is always the same one, and the maintainers do not have to bump all the baselines at each release.

#### Discussion: is removing a dependency a compatible change?

In the example, `C 1.2` depends on `E` and `C 1.3` no longer does. Is `C 1.3` still compatible with `C 1.2`? This question led to a discussion during the talk. A participant gave a real case: Telescope dropped its dependency on collection extensions because it no longer needed them. Is this a new major version?

The answer is that semantic versioning is about what a project promises. If the maintainer of `C` considers that `C` still offers the features that are documented, replacing `E` by `F` is compatible. If `B` uses `E` directly, and does not declare it because it knows that `C` will load it, the bug is in `B`: it has to declare the dependency. Clear guidelines are needed here, and a checker would help.

A similar problem exists with the order of packages inside a baseline. Packages may be loaded in the right order only because they were written in that order, for example SUnit and then some tests, without the baseline stating that the tests depend on SUnit.

### Putting MVS in Pharo

The algorithm alone is not enough. The rest of the chapter describes the seven pieces of the integration.

| Piece | Content |
| --- | --- |
| 1. MVS | the algorithm described above |
| 2. Resolver | a resolution step before the load |
| 3. Reading baselines | reading many baselines without changing the image |
| 4. Installed code | taking into account what is in the image |
| 5. Cleanup | dropping what nobody uses |
| 6. Findings and report | saying what is wrong, and what could be upgraded |
| 7. Roots and dev | forcing a version and working on branches |

### A resolution step

Until now a Metacello load was organized in three steps:

- _record_ walks the baselines from the root and builds the plan: which packages, in which order, with which preLoad and postLoad. It also chooses each version on the way, through the handlers or a popup,
- _fetch_ downloads the packages that the plan needs, without loading anything,
- _load_ loads the packages into the image, in order.

Dependencies were resolved during _record_. The new version cuts _record_ in two parts and adds a step before it, as shown in Figure *@figpipeline@*.

![The steps of a load, before and now.](figures/pipeline.png width=90&label=figpipeline)

- _resolve_ chooses one version of every project and loads nothing. A resolution with errors stops here,
- _record_ builds the same plan as before, but it decides no version: it takes the versions of the resolution,
- _fetch_ and _load_ work as before. In addition, _load_ installs the `BaselineOf` classes and registers every project it loaded.

The resolver is pluggable. The old policy is called the _interactive_ resolver, since it asks the user each time it finds something. It is the default, so the change is backwards compatible. The other resolver is the MVS one.

Splitting the process fixed a few issues on the way:

- preLoad and postLoad run once per load (they ran twice),
- a dependency cycle is an error (the load was hanging),
- a project asked at two versions is loaded once (both versions were loaded in turn).

### Reading baselines without touching the image

To choose, MVS has to read many baselines. In the example, seven versions are reached, therefore seven baselines have to be read before anything is chosen. This includes the baselines of both `C 1.2` and `C 1.3`.

Before, reading the baseline of `C` at `v1.3` meant to check out `v1.3` in the working copy and then to load `BaselineOfC` in the image. Both the working copy and the image change, for every version read. When `v1.2` is read and then `v1.3`, the class in the image is overwritten.

Now the versions of a baseline are read from git, without a checkout, and loaded as anonymous subclasses, in what the implementation calls a _sandbox_ (Figure *@figreading@*). Nothing is installed in the main namespace, so the image does not become dirty. Extensions are left out. The real `BaselineOf` class is installed after the load, at the chosen version.

![Reading a baseline, before and now.](figures/reading.png width=85&label=figreading)

### Taking installed code into account

What happens when a version of a project is already in the image? Suppose that `F` is already installed and that you load `A 1.0`.

Before, Metacello called the `onUpgrade:` block when the incoming version is newer than the one in the image, and the `onDowngrade:` block when it is older:

```language=pharo
Metacello new
	baseline: 'A';
	repository: 'github://me/A:v1.0';
	onUpgrade: [ :ex | ex useIncoming ];
	onDowngrade: [ :ex | ex useLoaded ];
	load
```

Depending on the handlers, Metacello can replace installed code, even with an older version. This may be dangerous.

With MVS, what is installed counts as one more requirement of the graph. The highest version is selected, as for any other requirement. Installed code can therefore raise a version, but never lower it (Figure *@figinstalled@*).

![Installed code is a constraint: a project goes up when it is compatible, and never goes down.](figures/installed.png width=60&label=figinstalled)

If the image contains `F 4.1` and the baselines ask for `F 4.2`, `F` is upgraded. If the image contains `F 4.3` and the baselines ask for `F 4.2`, `F 4.3` is kept and nothing changes.

A project may also be installed from a branch or a commit, for example with Iceberg. Such a version cannot be compared with others, so this is an error and nothing replaces it. This is a conservative choice. Suppose that we upgrade Bloc in the image: what happens to the tools that use it? We come back to this in Section *@secopen@*.

### Cleaning up

Look again at the final tree of the example (Figure *@figorphan@*). `E 3.5` was selected because `C 1.2` asked for it. But `C` then went up to `1.3`, which does not ask for `E`. Nobody uses `E` and it is still in the list.

![`E` is an orphan: only the superseded `C 1.2` asked for it.](figures/orphan.png width=70&label=figorphan)

Go keeps `E`. This is not a problem for Go, since it only compiles what is imported. Metacello, however, would install the code of `E` in the image. Therefore a second pass walks again from the root `A`, but only through the chosen versions. Projects that are not reached are dropped (Figure *@figcleanup@*).

![The second walk goes through the chosen versions only. `E` is not reached and is dropped.](figures/cleanup.png width=65&label=figcleanup)

The projects finally loaded are `A 1.0`, `B 1.0`, `C 1.3`, `D 2.1` and `F 4.2`. The option `dropUnused: false` keeps `E`, like Go does.

### Findings and reports
@secfindings

Before, each problem was a notification or a popup in the middle of the load. The first one stopped the load, with half of the image already loaded. Now the resolution collects all the problems at once, before anything is loaded. They are called _findings_ and there are three kinds:

- an _error_: we cannot know what to load, so nothing is loaded,
- a _warning_: it loads, but it should be fixed. We can make a decision, and it is always the same one,
- an _info_: what you could upgrade. For example, you loaded Bloc 1.3 and 1.5 is available.

Figure *@figmoosefindings@* shows the findings for Moose v13.0.0 in the inspector.

![The Findings tab of the inspector, on the resolution of Moose v13.0.0.](figures/moose-findings.png width=80&label=figmoosefindings)

#### Errors

| Error | Example |
| --- | --- |
| No version asked | `C: github://me/C:master/src` |
| Two majors of one repository | `B` asks for `C v1.2.0`, `D` asks for `C v2.0.0` |
| One project from two repositories | `C` from `github://me/C` and from `github://fork/C` |
| Group not declared | `loads: #('UI')`, and `C` has no group `UI` |
| Baseline does not load | the baseline of `C` does not compile here |

_Two majors._ Pharo can load only one version of `C`. If `C 2.0` is loaded, `B` probably does not work, and if `C 1.2` is loaded, `D` does not work (Figure *@figmajors@*). There is no good choice, so it should not be made silently.

![Two major versions of the same project cannot be reconciled.](figures/majors.png width=80&label=figmajors)

_Two repositories._ When a project is asked from its repository and from a fork, nothing guarantees that the two agree, even for tags with the same name.

_Baseline does not load._ Many old baselines contain code that no longer works.

There is no handler to ignore an error, since there is nothing sensible to load. It is possible however to override a project for one load, as explained in Section *@secdev@*. This covers in particular the first three errors of the table. It is not reproducible, since it is an override.

A participant mentioned another known conflict. The bootstrap of Pharo first installs Tonel from a local clone using FileTree, because remote repositories are not supported yet at that point. It then has to flush the registry before loading the Pharo baseline, which refers to Tonel on GitHub.

#### Warnings

| Warning | Example |
| --- | --- |
| Floating version | `C:v1.x.x` is taken as `v1.0.0` |
| Version not written vX.Y.Z | `C:1.02` instead of `C:v1.2.0` |
| Project required under a second name | a second name, `C2`, declared with `project:copyFrom:with:` |
| Repository string writes a path | `github://me/C:v1.2.0/src`, the path is ignored |

Warnings work as deprecations: the code still loads, the report shows the way forward, and a later version can turn them into errors.

_Floating version._ `v1.x.x` is a tag that moves. Today it points to something, and tomorrow it may point to something else, so it is not reproducible. MVS reads it as `1.0.0`: you declare to be compatible with all the versions of the series. We come back to it in Section *@secfloating@*.

_Version not written vX.Y.Z._ Many projects do not follow the format of semantic versions. Does `1.02` mean `1.2.0` or `1.0.2`? Some projects use a letter as a suffix. When such a version can be parsed somehow as a semantic version, it is, with a warning.

_Second name._ Declaring a project as a copy of another one is an unusual feature. Its purpose was not clear to the people present.

_Path._ The path to the sources, such as `/src`, is only useful for Tonel and FileTree repositories. When the dependency is in an Iceberg repository, the repository knows where its sources are. The path given from the outside is therefore ignored. This way a project can move its sources to another directory without breaking the projects that depend on it, which caused large problems in the past.

#### Where is the problem?

Each finding says which repository and which versions are concerned, and which baseline made the request. Findings can be browsed in the inspector, on the resolution. The same content is available as text, for the command line and the CI. `resolution report` returns the short version:

```language=text
1 errors, 1 warnings, 1 infos
Check verbose report for issue details

----------
Errors (1)
----------
Two majors of one repository (1)
  - C: v1.2.0 and v2.0.0 are required
```

`resolution verboseReport` also tells who required what, and what could be upgraded:

```language=text
Two majors of one repository (1)
  - C: v1.2.0 and v2.0.0 are required
    Required by: A 1.0, B 1.0
    Required by: A 1.0, D 2.1

---------------
Information (1)
---------------
B 1.0 can ask for
  - C v1.4 instead of v1.2
```

#### The graph

The inspector also shows the graph of the resolution. Figure *@figtoplo@* redraws the one of Toplo v0.11.0. Toplo depends on Album and on Bloc, and Album depends on Bloc too. The direct dependency from Toplo to Bloc is not redundant: the day Album no longer depends on Bloc, Toplo still does.

![The resolution of Toplo v0.11.0.](figures/toplo.png width=95&label=figtoplo)

Figure *@figtoplofindings@* shows the findings of this resolution: there are only warnings and infos. For example, XMLParser asks for `BitmapCharacterSet:v1.2.x`, but the project is already selected at `1.2.7`, and XMLParser could ask for `v1.2.9`.

![The findings of Toplo v0.11.0.](figures/toplo-findings.png width=80&label=figtoplofindings)

### Roots and dev mode
@secdev

We now look at the needs of the developers: forcing a version, and working on a branch.

#### Activating MVS

The message `mvs` activates minimal version selection in a load script:

```language=pharo
Metacello new
	mvs;
	baseline: 'Toplo';
	repository: 'github://pharo-graphics/Toplo:v0.11.0/src';
	load
```

Using `resolve` instead of `load` chooses the versions without loading anything. It returns the resolution, which can be inspected or asked for its reports.

#### Forcing a version: several roots

Before, a script had a single baseline. To force a version of `C`, you would load `C` first and then load `A`, keeping what is loaded:

```language=pharo
Metacello new
	baseline: 'C';
	repository: 'github://me/C:v1.4';
	load.
Metacello new
	baseline: 'A';
	repository: 'github://me/A:v1.0';
	onUpgrade: [ :ex | ex useLoaded ];
	load
```

Now a load can have several roots, with the new message `baseline:repository:`. Note that there is no semicolon between the two keywords in the line about `C`:

```language=pharo
Metacello new
	mvs;
	baseline: 'A'; repository: 'github://me/A:v1.0';
	baseline: 'C' repository: 'github://me/C:v1.4';
	load
```

The second root is one more requirement: the user requires `C` at least at `1.4`. It is the highest minimum, so `C 1.4` is selected (Figure *@figroots@*). This upgrades a dependency that is far in the graph without touching anybody's baseline, and only for this load.

![A second root raises `C` for this load only.](figures/roots.png width=72&label=figroots)

#### Working on a branch: dev mode

Before, a project could be locked to a repository:

```language=pharo
Metacello new
	baseline: 'C';
	repository: 'github://me/C:main';
	lock
```

`lock` pins a registered project to a repository. But a locked project that is not loaded yet is skipped.

With MVS, versions are always version numbers. Branches are only available through _dev mode_, for one load, with the message `dev:repository:`:

```language=pharo
Metacello new
	mvs;
	baseline: 'A'; repository: 'github://me/A:v1.0';
	dev: 'C' repository: 'github://me/C:main';
	load
```

- `C` comes from `main` for the whole load: it replaces every request of `C` (Figure *@figdev@*).
- Every dev project is a root.
- Dev mode is not contagious: the dependencies of `C` stay at their versions.
- Dev mode does not override installed code.

![In dev mode, `C` from `main` replaces every request of `C`. Its dependencies are not in dev mode.](figures/dev.png width=90&label=figdev)

The baselines remain the stable and reproducible ones, and the developer controls locally what is under development.

Dev mode is for development only. If you want to reproduce a build, do not use it.

#### Choosing the boundary

When you develop Toplo, do you want to edit Toplo and Bloc? Also Album and Alexandrie? Do you want the latest XMLParser too? Only the developer can tell where the development environment stops. It also depends on how well the packages are split: one would often like to develop only Bloc, but it does not work in practice.

Since dev mode does not spread, all the projects inside the boundary are listed. In the following script the `dev` branch of Toplo asks for the `master` branch of Album, and the `master` branch of Bloc asks for Alexandrie and XMLParser on `master`. They are therefore put in dev mode too:

```language=pharo
Metacello new
	mvs;
	dev: 'Toplo' repository: 'github://pharo-graphics/Toplo:dev/src';
	dev: 'Bloc' repository: 'github://pharo-graphics/Bloc:master/src';
	dev: 'Album' repository: 'github://pharo-graphics/Album:master/src';
	dev: 'Alexandrie' repository: 'github://pharo-graphics/Alexandrie:master/src';
	dev: 'XMLParser' repository: 'github://pharo-contributions/XML-XMLParser:master/src';
	resolve
```

It resolves with 0 errors, 14 warnings and 10 infos. The same can be done from the command line:

```language=bash
pharo Pharo.image metacello install --mvs \
  --dev Toplo github://pharo-graphics/Toplo:dev/src \
  --dev Bloc github://pharo-graphics/Bloc:master/src \
  --dev Album github://pharo-graphics/Album:master/src \
  --dev Alexandrie github://pharo-graphics/Alexandrie:master/src \
  --dev XMLParser github://pharo-contributions/XML-XMLParser:master/src
```

### In the CI: the case of Toplo

A pull request on Toplo ([https://github.com/pharo-graphics/Toplo/pull/413](https://github.com/pharo-graphics/Toplo/pull/413)), open at the time of the talk, uses all this in the CI. First, it changes the baseline of Toplo to ask for fixed versions: Bloc `v3.0.0` and Album `v0.11.0`. Then it adds a GitHub workflow with two jobs, `dev` and `integration`. The names can be changed.

```language=yaml
jobs:
  dev:
    uses: ./.github/workflows/pharo-ci.yml
    with:
      name: dev
      install: --dev Toplo gitlocal://$WORKSPACE
      tests: Toplo.*

  integration:
    uses: ./.github/workflows/pharo-ci.yml
    with:
      name: integration
      # XMLParser is not ours to follow: Bloc's dev branch asks for its master,
      # so it is put in dev mode at its released version.
      install: >-
        --dev Toplo gitlocal://$WORKSPACE
        --dev Bloc github://pharo-graphics/Bloc:dev
        --dev Album github://pharo-graphics/Album:dev
        --dev Alexandrie github://pharo-graphics/Alexandrie:dev
        --dev XMLParser github://pharo-contributions/XML-XMLParser:v3.6.3
      tests: Toplo.*
```

Both jobs run for each commit, in parallel (Figure *@figtoploci@*):

- The `dev` job loads the current commit of Toplo and respects the versions that its baseline asks for.
- The `integration` job loads the current commit of Toplo with the latest commits of Bloc, Album and Alexandrie. XMLParser is given in dev mode at a fixed version, because the development version of Bloc asks for its `master`, which does not work.

![The two builds of Toplo: two boundaries for the same baseline. Orange nodes are in dev mode.](figures/toplo-ci.png width=90&label=figtoploci)

The integration job is equivalent to having dependencies to branches, except that the baseline is never touched. The boundary is explicit in the job, and there can be several of them.

Each job installs the projects, produces the report (the short one for the pull request, the verbose one as an artifact), runs the tests, and fails on errors only. Once this is integrated, the report of Metacello should appear in the pull request for each commit.

#### Upgrades as issues

Another job runs once per week. It looks at the possible upgrades and opens an issue that lists them. Nothing is upgraded without a decision. This is less intrusive than modifying the baselines, and modifying them automatically is difficult anyway. It would be simple if baselines were purely declarative, but as soon as people write code inside a baseline, finding and replacing text no longer works.

#### Version numbers or commit hashes?

Some projects hardcode commit hashes in their baselines, to be reproducible without creating tags all the time. In both cases a tool is needed to produce something. But with version numbers the report can say that `B` could use `C 1.4` instead of `C 1.2`. With hashes you never get this information, since you do not know which is the next possible stable version. For a distributed set of projects, this is valuable.

### On real projects
@secreal

MVS was run on many projects: Toplo, Bloc, Spec, NewTools, Iceberg, Seaside, Roassal, Moose, Microdown, Pillar, the Bootstrap and Material Design Lite projects, and others. Most of the warnings come from this exercise: each case led to the question of whether compatibility could be kept.

Twenty real projects were recorded, with their versions and baselines. The tests replay them offline, without the network.

#### Toplo: the easy case

```language=text
pharo Pharo.image metacello install --mvs \
  github://pharo-graphics/Toplo:v0.11.0/src Toplo

0 errors, 15 warnings, 3 infos
Check verbose report for issue details

Warnings (15)
  Baseline asks the image (2)
  Baseline depends on the Pharo version (1)
  Floating version, taken as the first of its series (2)
  Project required under a second name (1)
  Repository string writes a path (8)
  Version not written vX.Y.Z (1)
```

Toplo v0.11.0 has some warnings, and it loads cleanly in Pharo 15. The live demo gave 14 warnings (Figure *@figtoplofindings@*) because the path `/src` had been removed from the script.

#### Moose: the hard case

```language=text
pharo Pharo.image metacello install --mvs \
  github://moosetechnology/Moose:v13.0.0/src Moose

14 errors, 62 warnings, 31 infos

Errors (14)
  Baseline does not load (1)
  Group not declared (3)
  No version asked (6)
  Not a repository with versions (2)
  One project from two repositories (1)
  Two majors of one repository (1)
```

The default release of Moose does not load with MVS. Figure *@figmoosegraph@* shows its graph: a red edge points to a problem, a yellow one most likely to a warning, and a dashed edge means that there are two dependencies to the same project.

![The resolution of Moose v13.0.0, as a graph.](figures/moose-graph.png width=80&label=figmoosegraph)

The errors of Figure *@figmoosefindings@* are of several kinds. An old version of FamixQueries, v1.0.0, does not load because its baseline refers to `RPackageOrganizer`, which no longer exists in this Pharo. Three groups are not declared, in Hashtable, Iterators and TreeQuery. Six dependencies, such as Fame, Famix or Units, name no version.

MVS does not fix Moose by itself: the baselines of Moose have to raise their minimums. The report lists what to raise: 17 newer versions in the same major, 5 newer majors, and 6 versions that fix an error. For example:

```language=text
Fame v1.0.0 can ask for
  - Hashtable v1.0.5 instead of v1.x.x
  - Iterators v1.14.0 instead of v1.x.x
  - TreeQuery v1.6.0 instead of v1.x.x
```

Not all of them can be applied blindly. FamixReplication asks for TinyLogger 1.x, and there is a new major version of TinyLogger. This has to be tested before upgrading.

#### Discussion: what does v1.x.x mean?
@secfloating

The missing groups of Moose led to a discussion, since these groups exist in the versions that Moose loads today. The two points of view are shown in Figure *@figfloating@*.

![Two readings of `v1.x.x`, when a group is added in the middle of the series.](figures/floating.png width=95&label=figfloating)

For the maintainers, `v1.x.x` is a tag that they move at each release: it always denotes the _latest_ version of the series. A group introduced in version 1.4 is always there, since nobody goes back to an older version.

Read as a semantic version, `1.x.x` means any version of the series, and MVS takes the _lowest_ one. If a project uses a group that was added in 1.4, it is not compatible with every `1.x.x`. It depends on 1.4 or later, and it should say so. There were also cases in practice where the tag had not been moved to the latest version.

Both sides agreed on one point: nobody should move tags by hand. This should be automated.

A participant explained where these tags come from. Metacello has a wildcard notation, such as `v1.?`, that is supposed to load the highest minor version. It does not really work: the request is lazy, so each access queries GitHub and the limit of the API is reached. The `x.x` tags were introduced to get the same effect without these requests. None of the projects examined uses the question mark, therefore MVS has no warning for it. The participant proposed to deprecate it.

### Open design issues
@secopen

Some cases need more complex decisions, and none of the solutions was convincing. The implementation follows a conservative path: each of them is an error for now. This is safe by default, and can become a design decision later.

_A conflict with what is already loaded._ Upgrading or downgrading installed code is dangerous. If the project is an XML library that is not being used, nothing happens. If it is Bloc, the tools may stop working, including the tool that renders what you are looking at. If the project has registered announcements, expect fireworks. In this case nothing is loaded, and it is better to start from a clean image.

_A dirty project in the image._ You loaded a project and then modified its code. Should a load overwrite your changes? An error is probably the right answer. A participant observed that you should always be in a saved state before an update.

_Dev projects and installed code._ Can a dev project override installed code, or be in conflict with it? One possibility is that everything that is loaded is added as a dependency, manually or automatically, and that the load uses what is in the image and gives a warning. An override from the outside remains a risk: when you load Toplo with another version of Bloc, who knows whether they are compatible?

_The same project from two repositories._ Some people copy the projects they depend on, to be sure to load only from repositories that they control. Two repositories may have tags with the same name for different code. An override can be used in this case.

_Installed, with no known version._ The project in the image cannot be compared with what the baselines ask for.

_Baselines that ask the image._ Some baselines contain code that queries the system: the Pharo version, `Smalltalk`, the environment. Most of these cases are in custom project attributes, or perhaps in postLoad code. The resolution may then differ from one image to another, so it is not reproducible. This has no solution yet, and it is a warning.

None of this affects existing users: without MVS, Metacello works as before.

### What comes next

Two perspectives were discussed.

_Metacello and git._ The core of the resolver knows nothing about git, branches or commits. It only knows versions: it asks a project for its version numbers, and Iceberg answers with its tags. Other sources of versions can be plugged in. With a catalog that knows the available versions of each package, it would be possible to resolve without going to git, and to load from zip files and some metadata. In the long term, the place where we load code from should be independent of GitHub. Source revision control and a database of code to load are two different things.

_Loading time._ Compiling the whole of Bloc again takes three or four seconds, while loading it takes a lot of time.

### Conclusion

- _Same load, same versions._ Versions are chosen before touching the image, and the same load always chooses the same ones.
- _Nothing goes up by itself._ An upgrade is explicit, and the report tells you what to raise.
- _Steps._ A load is made of resolve, record, fetch and load, with pluggable resolvers.
- _It is in Pharo, try it_: `metacello install --mvs`. Complex design issues are errors for now, on purpose.
