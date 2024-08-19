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

In Pharo, almost all computations are done by sending messages [cite @Berg11d].
Allocating an object is done also by sending a message.
In Pharo 13, we identified 14 allocation methods.

We instrumented these 14 allocator methods to intercept whenever they are invoked using MethodProxies (cite).
We use MethodProxies as the instrumentation back-end of Illimani.
MethodProxies allows one to decorate and control the execution of a method: execution an action before and after a method's execution.
When a sender requests an object allocation, the instrumentation captures the execution before the object is returned to the sender.
Inside the instrumentation, we capture the exact allocation time and an object’s model is created that will hold the object’s allocation information.
The MethodProxies architecture ensures that the code will be uninstrumented after the profiling is finished.
None of the allocations that are made in the process of extracting the information are intercepted.

### A glance over the UI

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

![Allocation paths](figures/allocations-second-allocator-without-palette-by-classes.pdf label=figAllocationsWithoutPaletteByClasses)

On the one hand, Figure *@figAllocationsWithoutPaletteByClasses* shows that the class `GrafPort`, the second most allocator, allocates all of its objects in the first moment and then stops allocating.
On the other hand, the other four classes allocate the objects continuously during the execution.
These different execution paths are identifiable thanks to the allocation path chart.
This accumulative chart is available in the Illimani's UI.

### Use Case: Identifying Allocation Sites
@secUseCaseColorPalette

A Pharo expert had a hint about a memory leak of objects of the type `Color`.
Illimani provides the possibility of filtering the profiling for a given specific domain.
We configure the profiler to capture all `Color` allocations.
We run the profiler on Pharo 11, commit `1a5afe1`.

Our target application was *MorphicUI*, a graphics framework for Pharo.
It has 669 classes with 11236 methods in Pharo 11.
We opened 30 Pharo core tools and we let each of the instances of the tools render for 100 Morphic rendering cycles.
Through this we are able to control how many times each of the tools is rendered, making the profiling reproducible.
The tools are: Iceberg, Playground, and the Pharo Inspector.
We opened 10 of each making 30 in total.

![The 5 top most allocator classes](figures/allocations-second-allocator-without-palette-by-classes.pdf label=figTopFiveAllocators)

Figure @figTopFiveAllocators presents an allocation paths plot for the top 5 allocator classes.

One can observe that the class `PharoDarkTheme` is the allocation site with the most allocations.
`PharoDarkTheme` is a subclass of `UITheme`.
`UITheme` is a central class in Pharo that is responsible for setting drawing configurations and also to provide the theme colors that are used in the Pharo IDE.

During the application's execution, we observed 23,686 total `Color` object allocations.

Table *@tabTopAllocationsBaseline* shows that the `PharoDarkTheme` class is responsible for 66% of all the `Color`.
Using the customizable queries of Illimani we analyzed the allocated objects by the UI Theme and we detected that only 15 out of 23,686 colors were different, meaning that 99,9% of the allocations were redundant.

@tabTopAllocationsBaseline
|    **Allocator class**   |  **Allocated colors** |   **%** 
|  --------------------------- | ----------------- | ---------
|      PharoDarkTheme          |  15,629           |  66%
|         GrafPort             |  4,096            |  17%
|       RubScrollBar           |  1,842            |  8%
|   GeneralScrollBarMorph      |  480              |  2%
|       TabLabelMorph          |  346              |  1%
|    Rest of the classes       |  1293             |  2%


Top 5 color allocations when opening 30 Pharo tools

**Summary:** Using Illimani we identified an allocation site in the class `PharoDarkTheme` that was allocating 66%of all the colors with 99,9% redundant allocations.

#### Color Palette

Looking at the implementation of `UITheme` we identified the cause of the redundant allocations: each time that a user asks for a color, the `UITheme` class creates a new instance of it.
We developed a Color Palette as a solution.
The Color Palette lazily allocates the colors when they are requested by a user and caches them once created.
When the `UITheme` changes, for example changing from a dark theme to a light theme, the caches are invalidated and they are recalculated on demand.

With the Color Palette fix, we profiled again the same execution to compare the baseline implementation against the Color Palette.
In Table  *@tabbaselinevscolorpalette* and in Figure *@figallocations-second-allocator-with-palette-by-classes* we see that with the Color Palette implementation, the `PharoDarkTheme` does no longer allocate `Color`. objects.

![The 5 top most color allocator classes with the Color Palette implementation](figures/allocations-second-allocator-with-palette-by-classes.pdf label=figallocations-second-allocator-with-palette-by-classes)

Object Allocations in Baseline vs Color Palette implementation

@tabbaselinevscolorpalette
|     **Allocator class** |  **Baseline**  | **Color Palette** |  **Diff**
|  ---------------------- | -------------- |  ---------------- | ----------
|    `PharoDarkTheme`     |    15,629      |         0         |   $\infty$
|     `RubScrollBar`      |    4,096       |       4,096       |  1$\times$
|   `Total Allocations`   |    23,686      |       7,974       |  3$\times$


**Summary:** With the Color Palette implementation the `PharoDarkTheme` class does not longer allocates redundant colors.

## Other allocation sites

We profiled the same execution setup, opening 30 Pharo tools, this time not filtering the allocated objects but capturing all of the allocations.
We observe in Table *@taballobjectallocations* that the classes `Rectangle` and `Margin` are the ones that are allocated the most, summing 64% of all the allocations between them.
The methods `Margin\>\>#insetRectangle` and `Number\>\>#asMargin` are the two methods producing all of those allocations.
We did not investigate further the causes of these object allocation sites.
The heat map presented in Figure *@figHeatmapNew* shows the relationship between the most allocators and the most allocated for this profile. One observes that the method `Margin\>\>#insetRectangle` allocates mostly `Rectangle` objects while `Number\>\>#asMargin` allocates `Margin` objects.

Allocated Objects

@taballobjectallocations
|  **Allocated object class** | **Allocations** |  **%**
|  -------------------------|-----------| -----------------
|        Rectangle         |   699,625    |    45%
|         Margin            |  300,663     |   19%
|       ByteString         |   111,662    |    7%
|    OrderedCollection     |   78,474     |    5%
|       WriteStream        |   60,448     |    4%
|   Rest of the classes     |  314,480     |   20%

![Most allocators-allocated heat map](figures/heatmapNew.pdf label=figHeatmapNew)

**Summary:** Illimani reports other two object allocation sites that allocate objects of type [Rectangle]{.smallcaps} and [Margin]{.smallcaps} that represent 64% of the allocations.

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
