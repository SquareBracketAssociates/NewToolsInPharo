---
abstract: |
  Modern programming languages provide automatic memory management with
  an efficient garbage collector making the memory management of an
  application transparent to the developer. There is a need for
  practical tools to support developers in their understanding of the
  memory consumption of their applications. In this paper, we present a
  prototype version of Illimani: a precise object
  allocation profiler. It has a rich object model that provides
  information about the objects' allocation context, the evolution of
  memory usage, and garbage collector stress.

  We were able to find an object allocation site in the class
  [UITheme]{.smallcaps} that was making 99,9% redundant allocations. We
  developed a Color Palette cache at the domain level that removed all
  the redundant allocations. We were also able to identify 2 other
  object allocation sites in the methods
  [Margin\>\>#insetRectangle]{.smallcaps} and
  [Number\>\>#asMargin]{.smallcaps}.

---

## Illimani: A Memory Profiler
@cha:illimani

_Authors:_ Sebastian Jordan Montaño -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- sebastian.jordan@inria.fr and Guillermo Polito -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- guillermo.polito@inria.fr and Stéphane Ducasse -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- stephane.ducasse@inria.fr and Pablo Tesone -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- pablo.tesone@inria.fr

### Introduction
@secIntro

Modern programming languages, such as Java, Python, or Pharo, provide automatic memory management with an efficient garbage collector.
This makes the memory management of an application transparent to the developer.
Debugging memory issues is known for being a tedious activity [@Chis11a].
There is a need for practical tools to support developers in their understanding of the memory consumption of their applications.

In this chapter, we present Illimani : a precise memory profiler (cite illimani papers and GitHub) framework for the Pharo programming language [@Duca22c].
It serves to profile object allocations that are produced during the execution of an application.
It can also profile object lifetimes by attaching an ephemeron to the allocations.
It provides information about the allocation context for each of the allocated objects, the objects types, their size in memory, object lifetimes, the evolution of memory usage, garbage collector stress, among others.
It also has a sampling mechanism, the user can configure a sampling rate to not capture all object allocations and to avoid bloating the memory.

It runs on the stock unmodified Pharo's VM.
It instruments the object allocations methods to control their execution.
Each time that an object allocation is produced, Illimani captures it and register useful information about the allocation context, or the object lifetimes.
As a back-end, Illimani uses MethodProxies (cite method proxies paper and add a footnote for the github) which is a message-passing control library.
It also uses Ephemerons to know when an object is about to be finalized, estimating the object lifetimes.

We provide 2 uses cases in which we use Illimani.
In the first one, we profiled object allocation to detect hot allocation sites where redundant allocations were being made.
Our target application was the Morphic UI, a Pharo framework that is used to draw the Pharo IDE.
We were able to detect object allocation sites.
We found a color object allocation site in the class `UITheme.
We analyzed the allocated objects and we discover that 99,9% of the allocated colors were redundant.
We developed a Color Palette at the domain level introducing an important missing architectural element that serves as a natural cache.
With the Color Palette, we reduced the memory stress of the application by removing all the redundant allocations.

In the second use case, we use Illimani to profile object lifetimes in a memory-intense application.
We choose as a case study the loading of a 500 MB dataset into a DataFrame [ cite dataframe].
We have selected DataFrame3 library for our study because it is often used in memory-intensive applications such as machine learning, data mining, and data analysis [cite 12].
The profiler gave us object lifetimes.
We observed that our case study has 25% of long-lived objects that represent 40% of the allocated memory.
Applications that have many objects that live a fairly long time suffer from performance issues [cite 13 of df paper iwst].
Increasing the GC heap size has a significant impact on GC performance [cite df iwst 7 , 4 ].
With this information, we decided to tune the GC parameters to see if we can get performance improvements [cite 14, 13, 6].
We obtained improvements of up to 6.8 times compared to the default GC parameters when the number of full garbage collections is reduced

### Illimani Memory Profiler
@secIlli

Illimani[^3] is a memory profiler developed for the Pharo programming language that is available under the open-source MIT license.
Illimani profiles and extracts relevant information of the profiled application, such as the object lifetimes, objects' allocation context, memory usage, and garbage collector stress.
It presents this information with memory usage tables, accumulative allocation evolution charts, and a heat map visualization.
It is also possible to query the profiler to make a custom analysis.
Illimani is capable of filtering the profiling for a given specific domain.

![Illimani's user interface](figures/illi-ui.png label=figIlliUI)

Illimani offers the following features:

- Summary and statistics report
- Memory usage and lifetime tables with grouping capabilities
- Navigation of query results
- Heat map visualization with the relationship: allocator - allocated
- Accumulative allocation evolution

#### Summary and statistics report

Illimani provides a summary of the studied execution.
It provides information on the total allocated objects, the allocator classes and methods, the memory usage, and the garbage collector stress.

Illimani shows information on how many garbage collections were made, both incremental and full, and the time spent doing garbage collections.
Pharo has a two-generation garbage collector [cite @Unga84a].
It has a young and an old space.
The newly allocated objects are allocated in the young space and after they survive a threshold of garbage collections they are moved to the old space.
The garbage collections done in the old space are orders of magnitude slower than the ones done in the young space [cite @Poli23a; @Mira18a].

The profiler can groups the allocations by allocator classes or methods.
It shows this information in memory tables that can be sorted by the number of allocations or by the total memory size in bytes.

#### Memory usage and lifetime tables with grouping capabilities

Illimani can also present the information in form of memory tables.
These tables can show the absolute and relative number of allocation for allocation site, the size in memory of the allocations, the relative average object lifetimes, the allocated objects, among other information.
These tables can help the developer to easily identify the hot allocation sites of the objects that have a long average lifetime.
All of these tables can be filter to search for specific information by writing the object's class or the object's allocation site.
They can also be sorted according to the different fields.

![Memory table](figures/memory-table.png label=figMemoryTable)

Figure *@figMemoryTable* shows a memory table that groups the allocator (allocation site) with their total allocation (in total and relative numbers) and the size in memory that allocation occupy in memory (in total and relative numbers).
The table can be sorted in terms of the allocator's name, the total or relative allocations, and in terms of total and relative memory

![Objects lifetime table](figures/lifetimes-table.png label=figLifetimesTable)

Figure *@figLifetimesTable* shows the objects lifetime information in a table.
It groups the allocated object class by its average lifetime, percentage of allocations and the relative size of memory of all the allocations.
Similary to the previous one, it can be sorted by any of the table fields.

#### Navigation of query results

Illimani gives access to the raw information of the allocated objects such as the object lifetimes, the allocator class and method, the object's total size in memory, the object's allocation time, and its allocation context stack.
Pharo supports full-stack reification thanks to its reflective properties.
Illimani uses this language property to get all the senders that led to that object allocation.
The user can query Illimani to extract this information and to make a custom analysis.
We developed custom data structures with constant time insertion and accessing to support the queries.

```caption=Querying the profiler
"Allocations bigger than 4 KB"
profiler objectAllocations select: [ :e |
    e totalSizeInBytes > 4096 ].

"Most allocator methods grouped allocations"
profiler allocationsByMethod first groupedAllocations.

"Objects with a lifetime or more than 1 second"
profiler objectAllocations select: [ :e | e lifetimeAsDuration > 1 second ]
```

#### Heat map

Illimani can presents the allocation site information with a heat map visualization.
It shows the relationship between the most allocator methods and the most allocated objects.
Key questions developers ask about memory are related to who is responsible for most creating instances and of each class, or method [cite @Sill05a].
Heat map visualizations are particularly adapted to display such relationships.
Their matrix architecture supports the identification of key players: most created vs. most creating classes per entity [cite @Pauw02a; @Pauw00a; @Pauw94a].

The most allocators are ordered from top to bottom, the top is the one that allocates the most and the bottom one is the one that allocates the less.
The allocated classes are ordered from left, the most allocated, to the right, the less allocated.
This heat map supports a drill-down version where methods creating most objects are displayed instead of the classes:
Figure *@figHeatmapNew* shows that method `Margin>>#insetRectangle` is the one creating all rectangle objects.

![Allocator methods heat map](figures/heatmapNew.pdf label=figHeatmapNew)

#### Accumulative allocation evolution

Different executions have different allocation paths.
Illimani provides a chart with the allocation paths for the top allocators.
The number of top allocators is a customizable parameter that can be changed by the user.

![The 5 top most allocator classes](figures/allocations-second-allocator-without-palette-by-classes.pdf label=figAllocationsWithoutPaletteByClasses)

On the one hand, Figure *@figAllocationsWithoutPaletteByClasses* shows that the class `GrafPort`, the second most allocator, allocates all of its objects in the first moment and then stops allocating.
On the other hand, the other four classes allocate the objects continuously during the execution.
These different execution paths are identifiable thanks to the allocation path chart.
This accumulative chart is available in the Illimani's UI.

## Precise memory profiling []{#sec:preciseProfiler label="sec:preciseProfiler"}

In Pharo, almost all computations are done by sending messages (invoking
methods) [@Berg11d]. Allocating an object is done also by sending a
message. The methods [Behavior\>\>#basicNew]{.smallcaps},
[Behavior\>\>#basicNew:]{.smallcaps}, [Array class\>\>new:]{.smallcaps},
and [Number\>\>@]{.smallcaps} are the four methods that allocate objects
in Pharo.

Illimani automatically instruments the execution of the
profiled application to capture its object allocations. It instruments
the four allocator methods to control their execution before and after
being invoked. We use the library *MethodProxies*[^4] for instrumenting
the methods. *MethodProxies* add defined actions to be executed and or
after the method that is being instrumented.

Each time that one of those methods is invoked, Illimani
intercepts the call and registers important information about the
allocation context, the object's type, and its size in memory. Right
after the allocation is made, we store the allocated object's type, its
allocator class and method, and different information about the
allocation's context. The *MethodProxies* architecture ensures that the
code will be de-instrumented after the profiling is finished. None of
the allocations that are made in the process of extracting the
information are intercepted.

# Use Case: Identifying Allocation Sites []{#sec:useCase label="sec:useCase"}

A Pharo expert had a hint about a memory leak of objects of the type
[Color]{.smallcaps}. Illimani provides the possibility of
filtering the profiling for a given specific domain. We configure the
profiler to capture all the [Color]{.smallcaps} allocations that an
application creates. We run the profiler on Pharo 11, commit `1a5afe1`.

Our target application was *MorphicUI*, a graphics framework for Pharo.
It has 669 classes with 11236 methods in Pharo 11.

We opened 30 Pharo core tools and we let each of the instances of the
tools render for 100 Morphic rendering cycles. Through this we are able
to control how many times each of the tools is rendered, making the
profiling reproducible. The tools are: Iceberg, Playground, and the
Pharo Inspector. We opened 10 of each making 30 in total. The code to
reproduce the experiment is available as a script[^5].

Figure [1](#fig:allocations-second-allocator-without-palette-by-classes){reference-type="ref"
reference="fig:allocations-second-allocator-without-palette-by-classes"}
presents an allocation paths plot for the top 5 allocator classes. One
can observe that the class [PharoDarkTheme]{.smallcaps} is the
allocation site with the most allocations. [PharoDarkTheme]{.smallcaps}
is a subclass of [UITheme]{.smallcaps}. [UITheme]{.smallcaps} is a
central class in Pharo that is responsible for setting drawing
configurations and also to provide the theme colors that are used in the
Pharo IDE.

During the application's execution, we observed 23,686 total
[Color]{.smallcaps} object allocations.
Table [1](#tab:topallocationsbaseline){reference-type="ref"
reference="tab:topallocationsbaseline"} shows that the
[PharoDarkTheme]{.smallcaps} class is responsible for 66% of all the
[Color]{.smallcaps} allocations. Using the customizable queries of
Illimani we analyzed the allocated objects by the UI Theme
and we detected that only 15 out of 23,686 colors were different,
meaning that 99,9% of the allocations were redundant.

::: {#tab:topallocationsbaseline}
           **Allocator class**            **Allocated colors**   **%**
  -------------------------------------- ---------------------- -------
      [PharoDarkTheme]{.sans-serif}              15,629           66%
         [GrafPort]{.sans-serif}                 4,096            17%
       [RubScrollBar]{.sans-serif}               1,842            8%
   [GeneralScrollBarMorph]{.sans-serif}           480             2%
       [TabLabelMorph]{.sans-serif}               346             1%
    [Rest of the classes]{.sans-serif}            1293            2%

  : Top 5 color allocations when opening 30 Pharo tools
:::

[]{#tab:topallocationsbaseline label="tab:topallocationsbaseline"}

::: cbox
**Summary:** Using Illimani we identified an allocation
site in the class [PharoDarkTheme]{.smallcaps} that was allocating 66%
of all the colors with 99,9% redundant allocations.
:::

## Color Palette

Looking at the implementation of [UITheme]{.smallcaps} we identified the
cause of the redundant allocations: each time that a user asks for a
color, the [UITheme]{.smallcaps} class creates a new instance of it. We
developed a Color Palette as a solution. The Color Palette lazily
allocates the colors when they are requested by a user and caches them
once created. When the [UITheme]{.smallcaps} changes, for example
changing from a dark theme to a light theme, the caches are invalidated
and they are recalculated on demand. The Color Palette was integrated
into Pharo 11 in the commit `d540bcf`.

With the Color Palette fix, we profiled again the same execution to
compare the baseline implementation against the Color Palette. In
Table [2](#tab:baselinevscolorpalette){reference-type="ref"
reference="tab:baselinevscolorpalette"} and in
Figure [3](#fig:allocations-second-allocator-with-palette-by-classes){reference-type="ref"
reference="fig:allocations-second-allocator-with-palette-by-classes"} we
see that with the Color Palette implementation, the
[PharoDarkTheme]{.smallcaps} does no longer allocate [Color]{.smallcaps}
objects.

::: {#tab:baselinevscolorpalette}
         **Allocator class**          **Baseline**   **Color Palette**   **Diff**
  ---------------------------------- -------------- ------------------- -----------
    [PharoDarkTheme]{.sans-serif}        15,629              0           $\infty$
     [RubScrollBar]{.sans-serif}         4,096             4,096         1$\times$
   [Total Allocations]{.sans-serif}      23,686            7,974         3$\times$

  : Object Allocations in Baseline vs Color Palette implementation
:::

[]{#tab:baselinevscolorpalette label="tab:baselinevscolorpalette"}

::: cbox
**Summary:** With the Color Palette implementation the
[PharoDarkTheme]{.smallcaps} class does not longer allocates redundant
colors.
:::

![The 5 topmost color allocator classes with the Color Palette
implementation](figures/allocations-second-allocator-with-palette-by-classes.pdf){#fig:allocations-second-allocator-with-palette-by-classes
width="1.0\\linewidth"}

## Other allocation sites

We profiled the same execution setup, opening 30 Pharo tools, this time
not filtering the allocated objects but capturing all of the
allocations. We observe in
Table [3](#tab:allobjectallocations){reference-type="ref"
reference="tab:allobjectallocations"} that the classes
[Rectangle]{.smallcaps} and [Margin]{.smallcaps} are the ones that are
allocated the most, summing 64% of all the allocations between them. The
methods [Margin\>\>#insetRectangle]{.smallcaps} and
[Number\>\>#asMargin]{.smallcaps} are the two methods producing all of
those allocations. We did not investigate further the causes of these
object allocation sites. The heat map presented in
Figure [2](#fig:heatmapNew){reference-type="ref"
reference="fig:heatmapNew"} shows the relationship between the most
allocators and the most allocated for this profile. One observes that
the method [Margin\>\>#insetRectangle]{.smallcaps} allocates mostly
[Rectangle]{.smallcaps} objects while [Number\>\>#asMargin]{.smallcaps}
allocates [Margin]{.smallcaps} objects.

::: {#tab:allobjectallocations}
       **Allocated object class**       **Allocations**   **%**
  ------------------------------------ ----------------- -------
        [Rectangle]{.sans-serif}            699,625        45%
         [Margin]{.sans-serif}              300,663        19%
       [ByteString]{.sans-serif}            111,662        7%
    [OrderedCollection]{.sans-serif}        78,474         5%
       [WriteStream]{.sans-serif}           60,448         4%
   [Rest of the classes]{.sans-serif}       314,480        20%

  : Allocated Objects
:::

[]{#tab:allobjectallocations label="tab:allobjectallocations"}

::: cbox
**Summary:** Illimani reports other two object allocation
sites that allocate objects of type [Rectangle]{.smallcaps} and
[Margin]{.smallcaps} that represent 64% of the allocations.
:::

# Related work []{#sec:relatedWork label="sec:relatedWork"}

***Visualizing object allocation sites.*** Infante et al. [@Infa15a]
have developed a Pharo memory profiler that reports object production
sites and memory usage called Memory Blueprint. Memory Blueprint shows a
call graph with the methods that produce objects and a visualization of
the memory usage of the allocated objects. Their work focuses on
identifying object production sites while Illimani also
has a rich model for representing the object allocations that allows the
user to query them to calculate other statistics. It can be also queried
without the user interface as it is independent of it and it allows
inspecting the reified stacks of the allocation contexts. Fernandez et
al. [@Fern18a] made a visualization related to Memory Blueprint, but
that keeps the context of the method and the source code of it.
Illimani also provides for each of the allocated objects
the allocator method and class as well as the allocation context.
Fernandez et al. [@Fern22a] have developed a call graph visualization,
similar to their previous work but analyzing the memory consumption of
Python applications.

***Allocation matrix.*** De Pauw et al. [@Pauw94a] developed an
Allocation matrix, which is a visualization that shows the relationship
between the most allocators and the most allocated for the C++
programming language. We used this idea to implement our heat map
visualization.

***Resources consumption reduction.*** Bergel et al. [@Berg18a] have
worked on analyzing the memory footprint of the expandable collections
of Pharo. They analyzed the allocation of internal arrays and their use
to propose an optimized version of the expandable collections. Our work
is different but complementary in the sense that we profiled the memory
allocation of Pharo tools to identify allocation sites to reduce its
memory footprint.

***Domain specific profilers.*** Ressia et al. [@Ress12b] developed a
domain-specific profiler framework in Pharo that the user can specify
the profiled domain to allow the profiler to give more precise
information about the specific domain. They developed this technique to
profile a know performance issue that they had and the profiling tools
that were available at that moment were not sufficient to localize the
problem. The profiler that we developed allowed us to identify a problem
that we were not aware of. Thanks to its architecture,
Illimani also allows filtering the profiling for a given
specific domain. The user can specify which set of classes wants to
profile and which type of object allocations she wants to capture.

***Tracking of Allocation Sites.*** Odaira et al. [@Odai10a] have
working on tracking object allocation sites in Java. They developed two
new approaches to trace the object allocation sites with a minimum
slowdown of the execution. They store the allocation information on the
object hash code field or in the object header. They use the allocation
information to optimize the garbage collector copying directly into a
tenured space certain objects. Our work does not focus on the tracing
technique, we use method wrappers. Our solution does not require running
the profiler on a modified virtual machine and it has a rich model that
offers the possibility of extracting information from the allocation
context.

# Limitations []{#sec:limitations label="sec:limitations"}

In Pharo, there are special methods, called primitives that are executed
natively. At the moment of writing this paper, we were not able to wrap
these special methods. In Pharo 11 we identified in total 3 primitive
methods that allocate objects of classes [Array, Point]{.smallcaps} and
[Interval]{.smallcaps}.

Our profiler has an overhead of around 10$\times$. However, this not
affects the precession of the measurements as the application will make
the same number of allocations.

Illimani does 3 object allocations that are registered
during the profile. The number does not vary no matter the code that is
being profiled. This is not a significant perturbation for our profiles.

# Conclusion and Future Work []{#sec:conclusion label="sec:conclusion"}

Illimani is a memory profiler that can precisely capture
object allocations. It provides a rich object model that allows a user
to query and group the object allocations. Illimani also
shows the information with tables and visualizations. We profiled the
execution of opening 30 Pharo tools: Iceberg, Playground, and the
Inspector. We opened 10 times each making 30 in total and we let render
each of the applications for 100 Morphic cycles. We were able to detect
object allocation sites. Illimani reported that the class
[UITheme]{.smallcaps} was making 99,9% redundant object allocations. We
were able to fix the excessive allocations by introducing the
architectural concept of a Color Palette removing all the redundant
allocations that the [UITheme]{.smallcaps} was making.

We were able to identify other two allocation sites related to the
*MorphicUI* framework. For the same execution of opening the 30 Pharo
tools, 1,565,352 objects were allocated in total and the classes
[Rectangle]{.smallcaps} and [Margin]{.smallcaps} are the ones that are
allocated the most, summing 64% of all the allocations. The methods
[Margin\>\>#insetRectangle]{.smallcaps} and
[Number\>\>#asMargin]{.smallcaps} are the two methods producing all of
those allocations.

There is previous work done on energy profiling in Pharo [@Berg16b]. We
want to continue this work to include energy measurements along with the
object allocations. We will also develop a solution at the bytecode
level to be able to wrap the primitive methods too.

[^1]: The version of the tool and the technical report are dated March
    2023

[^2]: This work © 2023 is licensed under [CC BY 4.0
    ](https://creativecommons.org/licenses/by/4.0/)

[^3]: https://github.com/jordanmontt/illimani-memory-profiler

[^4]: https://github.com/pharo-contributions/MethodProxies

[^5]: https://gist.github.com/jordanmontt/05c51c5527bf1c8e375117a3b9020c1e
