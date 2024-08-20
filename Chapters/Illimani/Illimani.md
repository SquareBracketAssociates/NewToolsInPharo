## Illimani: A Memory Profiler
@cha:illimani

_Authors:_ Sebastian Jordan Montaño -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- sebastian.jordan@inria.fr and Guillermo Polito -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- guillermo.polito@inria.fr and Stéphane Ducasse -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- stephane.ducasse@inria.fr and Pablo Tesone -- Univ. Lille, Inria, CNRS, Centrale Lille, UMR 9189 CRIStAL, Lille, France -- pablo.tesone@inria.fr

### Abstract

Modern programming languages often feature automatic memory management with efficient garbage collectors, which aims to make memory management transparent to developers.
However, developers still require practical tools to gain insights into their applications' memory consumption.
In this chapter, we introduce Illimani: a set of mememory profilers designed to enhance memory profiling and garbage collection (GC) performance.
ILLIMANI provides detailed information about object allocation contexts, memory usage evolution, and GC stress.

We explain how Illimani works, we present its API and we provide two uses cases in which we use Illimani in real-life applications.

Our analysis using ILLIMANI revealed a critical object allocation site in the class `UITHEME`, which was responsible for 99.9% of redundant allocations.
To address this, we developed a Color Palette cache at the domain level, effectively eliminating these redundant allocations
Additionally, we identified two other significant allocation sites associated with the methods `MARGIN>>#insetRectangle` and `NUMBER>>#asMargin`.

In our second analysis, we used the object lifetime to analyze object lifetimes without requiring modifications to the Virtual Machine.
Our profiler, based on ephemerons and method proxies, tracks the duration of object allocations.
We applied this tool to a DataFrame application, observing a substantial number of long-lived objects.
By using this information to tune GC parameters, we achieved performance improvements of up to 6.8 times compared to default settings.

Together, these tools provide valuable insights for optimizing GC performance and application efficiency.
ILLIMANI helps in identifying and resolving redundant allocations.
It also offers actionable data for fine-tuning GC parameters and improving overall execution time.

### Introduction
@secIntro

Modern programming languages such as Pharo offer automatic memory management through garbage collectors (GC) [ 1 ].
This takes the responsibility of allocating objects and freeing the allocated memory from of the developer.
Pharo has a two-generation GC with a scavenging algorithm for the new generation and a stop-the-world mark-and-compact algorithm for the old generation [2, 3 ].
The Pharo GC periodically traverses the memory to detect the objects that are not reachable (an object is not reachable when it is no longer accessible nor usable). After the memory traversal, the GC frees the unreachable objects’ memory.

There are some applications in which a significant part of the execution time is spent in garbage collections.
The default GC parameters are rarely ideal for any given application [4].
Consequently, there is considerable potential for optimizing such applications to mitigate garbage collection overhead.

In this chapter, we present Illimani : a precise memory profiler (cite illimani papers and GitHub) framework for the Pharo programming language [cite @Duca22c].
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
We obtained improvements of up to 6.8 times compared to the default GC parameters when the number of full garbage collections is reduced.

**Chapter's outline** TO DO

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

Illimani is also a framework of memory profilers.
A user can implement his own profiler by subclassing the `IllAbstractProfiler` class and defining the few missing methods
Especially, the `internalRegisterAllocation:` method.
The `internalRegisterAllocation:` method will be called each time that an allocation is produced (or when sampling, each time that the sampling rates matches) with the newly allocated object as a parameter.
You can the `IllAllocationRateProfiler` class as an example of a very simple memory profiler.

Tthe profiler is independent from the UI, you can access to the same statistics and information, with out without the UI.
See the protocol `accessing - statistics` in the profiler to see the methods.
Also, the profiler has a statistics model that groups and sorts the allocation by class and by methods.

By default, when loading Illimani, it provides three implemented profilers: - allocation site memory profiler, - a object lifetimes profiler, - and an allocation rate profiler.
The allocation site profiler `IllAllocationSiteProfiler` gives you information about the allocation sites and where the objects where produced in your application.
The object lifetimes profiler `IllObjectLifetimesProfiler` gives you information about how much time did the objects lived, and about how many GC cycles (both scavenges and full GC) they survived.
The allocation rate profiler `IllAllocationRateProfiler` simply tells you the number of allocation and the duration of the execution.

#### Quick Getting Started

Profiling a given code snippet

```
profiler
	profileOn: [ 15 timesRepeat: [ StPlaygroundPresenter open close ] ] ;
	open;
	yourself
```

Profiling the Pharo IDE activity for a given amount of time

```
profiler
	profileFor: 6 seconds;
	open;
	yourself
```

Example 1, using the allocation site profiler for profiling the Pharo IDE activity

```
IllAllocationSiteProfiler new
	copyExecutionStack;
	profileFor: 6 seconds;
	open;
	yourself
```

Example 2, using the object lifetimes profiler on a code snippet:

```
IllObjectLifetimesProfiler new
	profileOn: [ 15 timesRepeat: [ StPlaygroundPresenter open close ] ] ;
	open;
	yourself
```

#### Common API

In this section, we will describe the Illimani's API.
This API is generic, meaning that it works for all the available profiler, and the future ones too.

##### Profile a code snippet or the Pharo IDE

You can decide both to profile a given method block or just watching the activity of the image for some time.

```
"With this the profiler will block the ui and you will only capture the objects created by your code snippet"
profiler profileOn: [ anObject performSomeAction ].

"With this the profiler with not block the UI nor the image. So, you will capture all the allocations of the image"
profiler profileFor: 2 seconds.
```

##### Profiler manual API

For starting the stoping the profiling manually. This can be useful if you don't know how long your program will run and you need to interact with the Pharo's IDE.

```
profiler startProfiling.
profiler stopProfiling.
```

##### Open the GUI

You can open the ui at any time with the message `open` (even if the profiler is still profiling)

```
profiler open.
```

### Sample the allocations

By default, the profiler captures 1% of the allocations. We chose this number because in our experiments we found out that the profiler producess precise results with minimal overhead with that sampling rate. You can change the sampling rate. The sampling rate needs to be a fraction.

```
"Capture 10% of the allocations"
profiler samplingRate: 1/10.

"Capture 100% of the allocations"
profiler samplingRate: 1.
```

##### Export the profiled data to files

You can export the data to csv and json files by doing:

```
profiler exportData
```

This will create a csv file with all the information about the allocated objects, and some other auxiliary files in json and csv. This auxiliary files can be the meta data about the total profiled time, the gc activity, etc.

##### Monitor the GC activity

You can monitor the GC activity while the profiler is profiling with the message `monitorGCActivity`. This will fork a process that will take GC statistics once per second. Then, when exporting the profiler data, two csv files will be exported containing both the scavenges and full GCs. By default, the GC monitoring is disabled.

```
profiler monitorGCActivity
```

### A glance over the functionalities

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

### Using Illimani in real life: use cases
@secUseCase

In this section we will describe two uses cases in which we use Illimani on real-life application to detect and fix memory issues.
We will start by using the allocation site profiler to identify hot allocation sites related to the Pharo's IDE.
Then, we will use the object lifetimes profiler to detect an memory performance issue in a memory-intensive application.

#### Use Case: Identifying Allocation Sites
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

##### Color Palette

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

##### Other allocation sites

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

#### Use case: Improving DataFrame performance through lifetime profiling

We evaluated our profiler by profiling the execution of loading a 500 MB CSV file into a DataFrame.
We choose DataFrame as our target application because it is a memory-intensive application that supports loading big files to do data engineering and machine learning.

We applied the following methodology for using the object lifetimes profiler:
We profile the execution of DataFrame and we then benchmark it to know how much time was spent on garbage collections.
Then, we choose non-default GC parameters taking into consideration the object lifetimes and the GC spent time.
If the profiler reports a significant quantity of long-lived objects, we choose non-default GC parameters that increase the memory heap and reduce the number of full garbage collections.
With these custom GC parameters, we benchmark again our target application.
We finally validate our profiler comparing the performance with the tuned GC parameters against the default ones.

##### Lifetime profiling results

The profiler gives a density chart of the object lifetimes.
We grouped the object lifetimes by intervals of one second.
All objects whose lifetime duration has the same second will be in the same bucket.
In Figure *@figDFLifetimes*, we calculated the density as a function of the actual memory size occupied by the objects.
We can observe that around 40% of memory stayed referenced for a long time.

![Object lifetimes profile by memory for a 500MB dataset](figures/df-lifetimes.pdf label=figDFLifetimes)

In Figure  *@figDFLifetimesTwo* we calculated the density but in function by the number of objects instead of the occupied memory.
Crossing this information with Figure 4 we get that 25% of the objects that represent 40% of the GC memory stay referenced for a long time.

![Object lifetimes profile for a 500MB dataset by number of objects](figures/df-lifetimes2.pdf label=figDFLifetimesTwo)

##### 4.3. Benchmarking DataFrame

We benchmarked the loading of a DataFrame but this time without the instrumentation.
We used the default GC parameters when running these benchmarks.
To improve the reproducibility of benchmarking, we used the best developer techniques for the benchmarks [cite 16 of df paper]: we cut the internet connexion and stopped all non-vital applications.
We run each of the benchmarks n-times and then we reported the average execution time with the standard deviation.
We benchmarked the loading of 3 CSV files of different sizes: 500 MB, 1.6 GB, and 3.1 GB.
We present the results of the benchmarks for the 3 different CSV files in Table *@benchmarkGCTime*.

@tabBenchmarkGCTime
| **Dataset** | **# of scavengers** | **# of full GCs** | **GC time**     | **Total time**     | **GC time in %** |
|-------------|----------------------|-------------------|-----------------|--------------------|------------------|
| 500 MB      | 266                  | 18                | 11 sec          | 1 min 11 sec       | 15%              |
| 1.6 GB      | 304                  | 36                | 1 min           | 4 min 8 sec        | 22%              |
| 3.1 GB      | 1143                 | 309               | 1 h 3 min 13 sec| 1 h 11 min 5 sec   | 89%              |

##### Tuning garbage collector parameters

Generational GCs suffer from poor performance when dealing with memory-intensive applications that generate numerous intermediate objects, which live a fairly long time under the default GC parameters [cite 17, 13 ].
Our profiler showed that DataFrame is an application that produces long-lived objects.
DataFrame has 25% of the objects that represent 40% of the allocated memory that live for a fairly long time (Figures *@figDFLifetimes*, *@figDFLifetimesTwo*).
One can reduce GC time by tuning the GC parameters [cite 6].
The benchmarks exhibited optimization opportunities by reducing the garbage collection time.
Generational GCs are not optimized for applications with a substantial number of long-lived objects.
Instead, they are specifically configured for applications where objects tend to die young [ cite 13].
We discussed with Pharo experts about Pharo’s GC implementation details.
With this internal knowledge of Pharo’s GC implementation and the DataFrame internals, we chose the a custom GC parameters.
We chose by hand this custom GC parameters that we knew will increase the heap size and reduce the number of garbage collections.
The Pharo GC has 4 available customizable parameters.
In Pharo, the heap size can be seen as the sum of the new and the old space. One can control the heap size by tuning these customizable GC parameters.

- Eden size represents 5/7 of the new space and it is where the objects are allocated; the other 2/7 of space is used for copying objects.
- Growth headroom is the minimum amount of space the GC will request to the operating system to allocate
- Shrink threshold is the amount of free space that the GC will manage before giving it back to the OS.
- GC ratio is a percentage that triggers a full garbage collection when the heap will grow that percentage.

_Note:_ For simplicity, in this section we only use one custom GC parameter.
Normally, one needs to use several and then comparing which one produces the best performance improvement.

##### Results 

Then as explained in the methodology, we benchmarked the loading of the DataFrame with the 3 different CSV files with the custom GC parameter configuration to see if we reduce the garbage collection time.
We obtained improvements of up to 6.8 times compared to the default GC parameter

In the following tables, we present the results that we obtained re-running the 3 benchmarks with the custom GC configurations.
For the 500 MB CSV, we got from the benchmark in Table *@tabBenchmarkGCTime* that 15% of the time is spent on garbage collecting.

We increased the performance up to 1.2 times for the 500 MB CSV file.
For the 1.6 GB CSV file, we increased the performance up to 1.2 times and 22% of the execution time passed doing garbage collections.

For the last CSV file, the one of 3.1 GB, we observe that we increased the performance up to 6.8 times.
This enhancement can be attributed to the fact that, for this 3.1 GB, 89% of the execution time is spent doing garbage collections. The custom configuration that we chose has a larger memory footprint compared to the default parameters.

Result with the custom GC parameter

@tabDFResults
| **Dataset CSV file** | **GC spent time**    | **Total execution time** | **Improved performance** | 
| -------------------- | ---------------------| ------------------------ |------------------------- |
| 500 MB               | 2.17 sec             | 60.58 sec                | 1.2 x                    |
| 1.6 GB               | 12.93 sec            | 3 min 20 sec             | 1.2 x                    |
| 3.1 GB               | 1 min 47 sec         | 9 min 42 sec             | 6.8 x                    |

# Conclusion and Future Work []{#sec:conclusion label="sec:conclusion"}

In this chapter, we presented Illimani, a sophisticated memory profilers set that accurately captures object allocations, object lifetimes, and provides a rich object model for querying and grouping these allocations
Illimani is also a memory profiler framework that users can use to craft their own memory profilers.
We showed the tool, along with its functionalities and its API.
We conducted two detailed use cases in which we use Illimani to tackle and solve real application memory and performance issues. 

First, we utilized the allocation site profiler of Illimani.
By profiling the execution of opening 30 Pharo tools—Iceberg, Playground, and the Inspector, each opened 10 times and rendered for 100 Morphic cycles—we identified significant allocation patterns.
Illimani revealed that the class `UITheme` was responsible for 99.9% of redundant object allocations.
This insight led to a solution where we introduced a Color Palette architectural concept to eliminate these redundant allocations.
Additionally, we discovered two other significant allocation sites within the MorphicUI framework.
Out of 1,565,352 total allocations, the classes `Rectangle` and `Margin` were responsible for 64% of these allocations, with methods `Margin>>#insetRectangle and `Number>>#asMargin` being the primary contributors.

Our second analysis was done using the object lifetimes profiler of Illimani.
This profiler was applied to a DataFrame loading three large CSV files.
Our findings revealed that 25% of the objects, which represent 40% of the memory, had relatively long lifetimes.
Based on these insights, and after discussing with Pharo experts about the GC implementation, we tested one different GC parameter configuration that increased the heap size.
Benchmarking these configurations showed performance improvements of up to 6.8 times compared to the default GC parameters.