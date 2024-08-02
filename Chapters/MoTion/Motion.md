## MoTion: A new Declarative Object Matching Approach in Pharo
_Authors:_ Aless Hosry -- EVREF, Inria Lille ord Europe, France -- aless.hosry@inria.fr and Nicolas Anquetil -- EVREF, Inria Lille ord Europe, France and Vincent Aranega -- Metacell, USA }

### Abstract 
Pattern matching is an expressive way of matching data and extracting pieces of information from it.
The recent inclusion of pattern matching in the Java and Python languages highlights that such a facility is more and more adopted by developers for everyday development.
Other main stream programming languages also offer pattern matching capabilities as part of the language (Rust, Scala, Haskell, and OCaml), with different degrees of expressivity in what can be matched.
In the meantime, in graphs, pattern matching takes a slightly different turn; it enhances the expressivity of the patterns that can be defined.
Smalltalk currently offers little pattern matching capability to find specific objects inside a large graph of objects using a declarative pattern.
In Pharo, the closest library to classical pattern matching that exists is the `RBParseTreeSearcher`, which allows to express specialized patterns over a Pharo Abstract Syntax Tree to find some inner node.
The question arises of what features a flexible pattern matching language should have.
In this chapter, we review the features found in different existing pattern matching languages, both in General Purpose Languages (like Java) and in declarative graph pattern matching languages.
We then describe MoTion, a new pattern matching engine for Pharo smalltalk, combining all these features.
We discuss some aspects of MoTion's implementation and illustrate its use with real case examples. 

### Introduction

The evolution of software engineering increasingly implies the need to search through data in memory and extract specific information in various domains, including _reverse engineering_ {!citation|ref=Gall95c!}, _analysis_ {!citation|ref=Thak17a!} and _model transformation_ {!citation|ref=Klin11a!}.
There are various techniques to help express precisely and succinctly what is searched and to perform the search after that.
Pattern matching is the process of checking whether a given pattern matches a given value or not {!citation|ref=Klin11a!}.
This technique can be used for ensuring that data has the right "shape", but also to search for and extract information from data.

Many General-Purpose Languages (GPL) incorporate this as a core feature (Haskell, Java, OCaml, Python, Rust, Scala) {!citation|ref=Hosr23b!}, one of the latest being Java, introducing officially Pattern Matching for switch expressions and statements in Java 17.
Graph pattern matching languages proved to be able to deal with a large variety and amount of data extracted from databases and represented in graphs.
They are famous for being able to express patterns in a declarative way and for enabling path traversals of nodes and edges deeply inside any graph {!citation|ref=Thak17a!}.
To simplify and make the pattern more declarative, some features are often implemented in graph pattern matching language, for example:

-   _Non-linear patterns_ allow developers to relate to found information many times in the same pattern, ensuring that a piece of data is actually in several places {!citation|ref=Egi22a!} (_e.g.,_ the `name` of a component must be the same as the name of one of its sub-components).

-   _Complex list patterns_ represent optional or repeated entities and allow developers to express a pattern over the shape of a list (_e.g.,_ ensuring that the last element is a specific value) {!citation|ref=Bast15a!}

-   _Deep recursive patterns_ allow developers to consider that two pieces of data must be connected through one or many intermediate data, which is particularly handy when dealing with recursive data.

In Object-Oriented programming, objects are structured data that can be matched based on their type and/or field values.
We refer to pattern matching in object-oriented languages as _object pattern matching_.
Similarities exist conceptually between pattern matching in object-oriented languages and graphs, but they do not support the same set of features.
More specifically, non-linear patterns, deep recursive patterns, and complex list patterns are currently not supported natively by pattern matching in object-oriented languages.
In this chapter we report on our efforts to implement a pattern matching extension to the Pharo programming language that supports all these features.
We explore an approach to pattern definition influenced by pattern matching for graphs and for objects to propose to developers a way of searching and extracting information from objects.
This is concretized in *MoTion>https://github.com/alesshosry/MoTion*, a novel object matching language implemented in Pharo.
MoTion allows the definition of declarative patterns, combining features from both worlds: pattern matching for graphs and for objects.
Using MoTion, developers can define flexible patterns, disregarding the depth of the information being searched for and the structure's complexity of any object.

### Motivation 
@secmotivation

When programming applications deal with large amount of data, developers often need to search for specific objects in the data.
This happens when working in real-world domains such as biology, transport and social networks.
An example of such graph analysis is illustrated by the work of Thakkar et al., describes how to extract the age of the eldest person knowing a person named "Marko" in a big graph of people {!citation|ref=Thak17a!}

Software engineering daily activities also involve searching for source code elements.
This is often done by representing the source code as a graph of objects (for example in an Abstract Syntax Tree) and searching for the "right object" inside this graph.
For example in {!citation|ref=Hosr23a!} Hosry et al. created a tool to detect dependencies between software elements, in a given system, that could be written in different programming languages.
This involves searching for software elements having very specific properties (eg. carrying a specific annotation for a Java element, or having a specific attribute in XML).
These software elements can be buried deeply in the graph of objects representing the whole system.
In another example, Mohamed and Kamel {!citation|ref=Moha18a!} describe how to reverse engineer an application, looking for design pattern instances.
For this, the authors suggested using static code analysis and following a set of heuristics, like identifying inheritance between classes and node selection inside methods based on their types.
Finally, searching is also needed when transforming (or refactoring, or restructuring) the code into a new form.
This can be done by looking for a specific software element and transforming it into a new one, or by modifying it in a new form {!citation|ref=Klin11a!}.

Doing this kind of search in a GPL (General Programming Language) means going through sets of objects, selecting some of them, and then navigating to their children looking for specific properties (like attributes with a given value), ...

A better solution for this is to use a pattern matching language that will allow describing the sub-graph of objects one is looking for and letting it find all the matching occurrences in the whole graph of objects.
The common pattern matching tools relieve the users from specifying how to traverse the whole graph, letting them concentrate on the description, in a specific notation, of the searched pattern.

```caption=Rascal Example&label=rascalExample
public ColoredTree
  makeGreen(ColoredTree t) {
    return visit(t) {
        case red(l, r) => green(l, r)
    };
}
```

%[[[label=rascalExample|caption=Rascal example
%public ColoredTree
%  makeGreen(ColoredTree t) {
%    return visit(t) {
%        case red(l, r) => green(l, r)
%    };
%}
%]]]

Listing *@rascalExample@* is an example extracted from the work of Klint et al. of a transformation rule expressed in Rascal, where method `makeGreen` defined in line 2 takes `ColoredTree t` as input parameter and replaces red nodes by green ones {!citation|ref=Klin11a!}.
The `visit` in line 3 is used to traverse all tree nodes and apply the rule expressed in line 4 using `=>` operator, where the Left Hand Side (LHS) pattern `red(l,r)` is transformed into the Right Hand Side (RHS) pattern `green(l,r)`.
This example illustrates the capabilities of pattern matching to represent the "shape" of data by describing a pattern: the LHS of line 4, and how information is extracted from this pattern: the `l` and `r` variables.

### Pattern Matching Techniques and Features Extraction 
@secSota

When it comes to pattern matching, two main approaches exist: pattern matching with graph query languages, and pattern matching in GPLs. Both of these approaches propose to the developer a set of possibilities when it comes to declaring a pattern, and how the result is returned. In this section, we review the work related to declarative matching over data in graphs and in GPLs.

#### Pattern Matching for Graphs

The main goal of graph pattern matching is to find all matches between a collection of pattern variables and target graph nodes that meet a set of requirements. 

According to Krause et al. {!citation|ref=Krau16a!}: A pattern is made up of a predicate set called a pattern graph, and an optional nested formula.
The pattern nodes, or the nodes of the pattern graph, are represented by a set of pattern variables over which the predicates and the formula are defined.
When a pattern is matched to a target graph, it means that (i) every pattern node is matched to a target node of the same type, (ii) every pattern edge is matched to a target edge of the same type, (iii) all predicates are satisfied, and (iv) the logical formula is satisfied.
This mapping of pattern variables to target graph nodes is referred to as the target nodes of the match.

A vast range of data from many domains can be represented by graphs {!citation|ref=Libk16a!} where Resource Description Framework (RDF) {!citation|ref=Worl14a!} graph and Property Graph (PG) {!citation|ref=Angl17a!} are commonly used to represent this data {!citation|ref=Deut22a!}.

An RDF graph is equivalent to a set of triples, of node-labeled edge-node, to represent the data {!citation|ref=Thak17a!} {!citation|ref=Deut22a!}, and SPARQL {!citation|ref=Worl13a!} is the language that is capable of handling large-scale analytical operations over RDF graphs {!citation|ref=Thak17a!}. It uses a syntax with patterns expressed in triple form (subject-predicate-object) {!citation|ref=Krau16a!} using a combination of variables and specific resources or literals. The objects and subjects match nodes, and the predicates match edges.

```language=sql&caption=SPARQL example&label=rdfQuery
SELECT DISTINCT ?name
WHERE {
  ?instance athlete ?athlete .
  ?instance medal Gold .
  ?athlete label ?name .
}
```

%[[[label=rdfQuery|caption=SPARQL example|language=sql
%SELECT DISTINCT ?name
%WHERE {
%  ?instance athlete ?athlete .
%  ?instance medal Gold .
%  ?athlete label ?name .
%}
%]]]

Listing *@rdfQuery@* is a simple example of a SPARQL query to extract the names of every gold medal (excluding duplicates) from an RDF graph (see Figure *@figSparqlData@*).
Line 1 is used to retrieve distinct (duplicates removed) names from the data returned by the query. 
The patterns are expressed in the `where` clause between lines 3 and 5.
Names suffixed by "`?`" are variables that can match any node in the graph. 
Line 3 matches `?instance` and `?athlete` to 2 nodes related by an `athlete` edge. 
Line 4 requires that the `?instance` also be linked to a `Gold` node by the `medal` edge. 
Line 5 matches the `?name` variable to the node related to the `?athlete` node through a `label`
edge. 
This `?name` is returned by the query (line 1).

![Example of a simple RDF graph](figures/sparql-data.png label=figSparqlData)

**Key points:**

-   SPARQL allows expressing the structure of the data looked for without worrying about how deep in the whole graph of data it is orvhow complex it is.

-   In lines 3 and 5, `?athlete` has been reused to match the same value multiple times in the same pattern.

-   Additionally, patterns are expressed in a declarative way allowing developers to add as many patterns as they need.

A PG models the data as a mixed multi-graph, where both nodes and edges can be labeled and attributed {!citation|ref=Deut22a!}. 
Various querying languages can be used for PGs like Gremlin APIs {!citation|ref=Rodr15a!}, and some declarative graph query languages like Cypher by Neo4j {!citation|ref=Fran18a!}, GSQL by TigerGraph {!citation|ref=Deut20a!}, PGQL by Oracle {!citation|ref=Simo22a!}, or Graph Pattern Matching Language (GPML) which is able to run CRUD operations {!citation|ref=Deut22a!}. 
In addition, there are some experimental solutions in both industry and academia, like G-CORE {!citation|ref=Angl18a!}.

Gremlin is considered a graph traversal language, allowing the exploration of complex relationships through various nodes in the graph using traversals like Recursive Traversal {!citation|ref=Rodr15a!}.

```caption=Gremlin recursive example&label=gremlinRecursive
    g.V().has("name","marko").
    repeat(out()).times(5).
    values("name")
```

%[[[label=gremlinRecursive|caption=Gremlin recursive example 
%    g.V().has("name","marko").
%    repeat(out()).times(5).
%    values("name")
%]]]
 
A Gremlin traversal is a sequential movement through the steps, which are represented by nodes and edges in a data graph. 
It initiates from all nodes in the graph and traverses the path until the endpoint predefined by the developer is reached successfully among the graph.
Listing *@gremlinRecursive@* is a recursive traversal expressed in Gremlin that consists of selecting 5 persons named _marko_. In line 1 `g.V()` is the starting point of the traversal where `g` refers to the target graph of the match and `V()` denotes all nodes selection of `g`.
Then, `.has("name", "marko")` filters the nodes to only those for which the property `name` is equal to _marko_. 
In line 2, `repeat(out())` will repeat the previous match to get all possible results. 
Then `.times(5)` limits the repetition to 5 occurrences. And finally for line 3, `values("name")` property of value name is retrieved after moving recursively five steps forward.

**Key points:**

-   The main advantage of this matching technique is that it helps the developers specify a path to be traversed, with unlimited numbers of nodes and edges. It is adopted by many other languages for matching PG graphs like Cypher and PGQL.

-   It is also possible to specify repeated searches to return all possible matches.

-   Repeated searches risk falling into an endless cycle in the presence of cyclic relationships. Therefore, they can be limited to a maximum number of repetitions using `times()`.

#### Pattern Matching in GPLs

Pattern matching is one of the main features of functional programming languages {!citation|ref=Ryu10a!} like *Haskell>https://www.haskell.org/tutorial/patterns.html*. With the evolution of object-oriented programming, pattern matching has increasingly found its way into this paradigm {!citation|ref=Kohn20a!}. 
General Purpose Languages now have pattern matching capabilities like Java, which implemented pattern matching in the *Amber>https://openjdk.org/projects/amber/*  project; *Python>https://peps.python.org/pep-0000/*; or *Rust>https://doc.rust-lang.org/book/ch18-00-patterns.html*.

Such languages involve matching objects based on their types and/or field values, and many of them introduced the conditional match like "`switch` _subject_ `case` _pattern_" in Java or Python.

```language=Java&caption=Java Pattern Matching Example (Java 21)&label=javaExample
record Point(int x, int y) { }
enum Color { RED, GREEN, BLUE; }
...
String typ;
switch (obj) {
  case null     -> typ="Null pointer";
  case String s -> typ="A String";
  case Color c  -> typ="A Color";
  case Point p  -> typ="A Point";
  case int[] ia -> typ="An Array of int";
  default       -> typ="Something else";
}
```

%[[[label=javaExample|caption=Java Pattern Matching Example (Java 21)|language=Java
%record Point(int x, int y) { }
%enum Color { RED, GREEN, BLUE; }
%...
%String typ;
%switch (obj) {
%  case null     -> typ="Null pointer";
%  case String s -> typ="A String";
%  case Color c  -> typ="A Color";
%  case Point p  -> typ="A Point";
%  case int[] ia -> typ="An Array of int";
%  default       -> typ="Something else";
%}
%]]]

Listing *@javaExample@* exposes a pattern matching example in Java, where object matching is applied using the `switch case` statement.
Lines 1 and 2, define the data structures that are used in the matching. 
Line 4 is a variable that will hold a description of the type of `obj` (line 5). The switch statement performs the matching by looking for the first `case` that will match `obj` in lines 6 to 11.

**Key points:**

-   Object pattern matching helps define structural objects to be matched.

-   Some languages allow to match an object not only on its structure, but also on the value an attribute should have.

We found several libraries that complement programming languages by introducing pattern matching capabilities. 
Tom {!citation|ref=Pier03a!} and Rascal {!citation|ref=Klin11a!} integrate with Java, and Kiama {!citation|ref=Sloa09a!} integrates
with Scala. 
Tom and Rascal cover features that were not covered natively by Java like _Path traversal_, _Recursive traversal_, _Object matching_ and _Complex lists_. Kiama and Rascal enable transformation through the definition of strategies. These strategies employ pattern matching to identify the terms requiring transformation. 
Strategy execution in Kiama can proceed in different directions either top-down or bottom-up. 
This capability opens up the possibility of traversal in various directions, but it still requires additional investigation concerning its relevance in pattern matching.

#### Pattern Matching Language Features

We now consider what features have been proposed in different pattern matching tools/languages. This will be an inspiration for designing our own pattern matching language.

Klint et al. {!citation|ref=Klin11a!} state that a rich pattern language should provide string matching based on regular expressions, matching of abstract patterns, and matching of concrete syntax patterns. 
To reach a stage where developers are able to express any pattern compatible with the shape of the object they are looking for, a list of "features" must be provided by the language and applied using multiple operators or methods.

Previously in the literature, some authors have listed features supported by Rascal or Python {!citation|ref=Klin11a!} {!citation|ref=Kohn20a!}.

We first consider features found in graph pattern matching. 
_Graph matching_ is famous for specifying patterns similarly to database SQL queries.

- _Declarative patterns_: help the developers define specific patterns that look like the results of matching, without caring about how these patterns will be matched. Using this paradigm leads to reduced development's time, increased maintainability, quick learning for pattern expression, and live preview changes without impacting the whole analysis process {!citation|ref=Imbu21a!}. We oppose it to _Imperative paradigm_ which consists of defining the computational steps to complete a task (the matching process).

- _Path traversal_: refers to visiting elements (i.e. nodes and edges) in a graph in some algorithmic fashion {!citation|ref=Rodr12a!}. It helps the developers traverse nested structures while matching patterns.

- _Recursive traversal_: is needed to apply recursive search over deep structures, especially when developers ignore the depth of elements being searched for.

- _Repeated search_: is a feature related to the number of returned matches, where some languages can repeat the search to find all possible matches found, while others stop searching after finding the first match. A more flexible solution offers to specify the maximum number of matches that are expected, allowing to repeat the search without incurring the risk of infinite loops.

We now consider additional features of object matching. 
Some of these features would not make sense in graph patterns (such as _object matching_). 
We also add here some features that are inspired by pattern matching in functional languages such as non-linear patterns:

- _Object matching_: is dedicated to match objects based on their types and properties, which can be methods with return values or instance variables.

- _Literals_: (strings, numbers, integers) simply match themselves. They can be used to specify the value of an object's property.

- _Non-Linear pattern_: (sometimes called _unification_) allows the developers to use the same variable multiple times that should always match the same value in the pattern.

- _Wildcards_: represent a placeholder, an anonymous property that can be matched and is not used afterwards.

- _Structural pattern_: allows sub-patterns definition inside a pattern.

- _Complex lists_: supports the matching of a sequence of patterns taking into consideration their order. For example specifying that a pattern must be matched at the end of a list or in the middle,...

- _Logical matcher_: allows the possibility of combining multiple patterns in a boolean expression.

- _Negation_: may allow to express a simpler pattern when searching for bindings that do not conform to a particular criteria.

#### Some existing Object Pattern Matching Languages

We studied existing pattern matching languages to understand what features they offer. 
The goal of our matching language will be to offer all these features. 
We limited ourselves to Object Oriented GPLs. 
We considered the top OO languages used in 2022 according to *Github>https://octoverse.github.com/2022/top-programming-languages* : C#, C++, Java, Javascript, Python, Ruby, Typescript (three more languages are not OO: C, PHP, Shell). 
We added Rust and Scala that are well known for their pattern matching capabilities. 
And we added a library in Pharo (RBParseTreeSearcher) because this is the language we are working with.

@tabobjectLanguagesTable
|Characteristics        |  C#  |  Java |   Pharo (4) |  Python |  Ruby |  Rust | Scala
| --------------------- | ---- | ----- | ----------- | ------- | ----- | ----- | -----
|_Paradigm_           |  D&I |   D&I |     I       |  D&I    |  D&I  |  D&I  |   D
|_Path traversal_     |      |       |             |    x    |       |   x   |   x
|_Recursive traversal_|      |       |      x      |         |       |       |      
|_Repeated search_    |      |       |      x      |         |       |       |
|_Object matching_    |   x  |  \(1\)|     \(5\)   |    x    |   x   |   x   |   x
|_Wildcard_           |   x  |   x   |      x      |    x    |   x   |   x   |   x
|_Structural pattern_ |   x  |   x   |      x      |    x    |   x   |   x   |   x
|_Complex lists_      |   x  |  \(2\)|      x      |         |   x   |       | 
|_Literals_           |   x  |   x   |      x      |    x    |   x   |   x   |   x
|_Logical matcher_    |   x  |   x   |             |    x    |   x   |   x   |   x
|_Negation_           |   x  |  \(3\)|             |    x    |   x   |       | 
|_Non-Linear pattern_ |   x  |   x   |      x      |         |       |       |

Table *@tabobjectLanguagesTable@* shows the features supported by different OO languages that have native pattern matching capabilities.

Without surprise, _Object matching_ is well supported. 
_Structural pattern_ and _Wildcard_ are also two features that are common. On the other hand, it shows that features like _Path traversal_, _Recursive traversal_, _Repeated search_, _Complex lists_ and _Non-Linear pattern_ are not universally supported by object matchers.

We are interested in creating an object matching language that could be used to match objects in models, taking into consideration that features like _Repeated search_, _Non-Linear pattern_, _Complex lists_, _Recursive traversal_ and _Path traversal_ are also important for such matching languages, in order to provide developers with the possibility to create patterns in a flexible way, allowing deep matching for deeply recursive models.

### MoTion
@secMotion

MoTion is a new object pattern matching language in Pharo. 
A pattern matching language works on a finite set of objects that we will call a _model_. Examples of models are: the Pharo AST of a method, the DOM of an XML document, the objects loaded from a JSON file,... 
MoTion can deal with Pharo objects independently of the model containing the data.
MoTion combines both features for graph pattern matching and object matching listed previously, and by doing so, it enables expressing patterns declaratively and applying matches to complex object structures.

In the next sections, we give a first overview of the pattern language with a concrete example. We also present the grammar of the pattern matching language and explain the semantics of each element of the language.

#### Simple pattern example 
@secPatternExample

Before explaining in detail the syntax of MoTion, we give a simple example of a pattern used to detect all classes or interfaces that
extend a given interface (named `’Remote’`). 
It works on Famix models.
Famix {!citation|ref=Anqu20a!} is a family of programming language meta-models that can represent programs. It is part of the Moose software analysis platform. 
FamixJava is the meta-model that allows representing Java programs, it defines classes such as `FamixJavaInterface` or `FamixJavaClass` that represent respectively Java interfaces and Java classes. 
These entities have properties like `name` that holds the name of an entity, or `superInheritance` that relate a class to its superclass.

```language=St&caption=External dependencies searching pattern&label=adonisPattern
FamixJavaModel % {
 #'allTypes>entities' <=> FamixJavaInterface % {  
   #'superInheritances>superclass>name' <=> 'Remote' .
   #'isStub' <~=> true.
 } as: 'foundInterface'.
}
```

The pattern starts by matching an instance of class `FamixJavaModel` (line 1) and looking in its `allTypes` property (line 2). 
This means that if it is not given a FamixJavaModel, it will not match anything.

`allTypes` returns a special object that is a wrapper around a collection of all types defined in the model (classes, interfaces,...). 
To get this collection, we use its `entities` property. 
Note that if the object returned by `allTypes` has no `entities` property, then the pattern just fails to match anything.

The result of line 2 is a collection of objects on which we apply the operator "`<=>`" with the sub-pattern in lines 3 to 7. 
The operator "`<=>`" is polymorphic and for a collection of objects, it will try to match its sub-pattern to any object in the collection.

This sub-pattern matches an object of class `FamixJavaInterface` (line 3), and looks in its `superInheritances` property (line 4), then in the `superclass` property of the returned object, then in the `name` property of this other returned object. Here again, the operator "`>`" is polymorphic and handles collections of objects (in the pattern `superInheritances>superclass`) differently than single objects (in the pattern `superclass>name`).

Line 5, if the name matches the string 'Remote' (the 'Remote' interface of Java RMI), the engine checks for the next sub-pattern (line 6) which states that the matched object of line 3 (an instance of `FamixJavaInterface`) should also have a `isStub` property that should not match the boolean `true` (this is different from saying it should match `false` because it could also be `nil`).

Finally in line 7, if a matching `FamixJavaInterface` is found, it is bound to the key `foundInterface` in the final result. This result will be returned, and the object matched can be retrieved from it.

#### MoTion Grammar 
@secGrammar

In this section we present the grammar of MoTion. 
It must be noted however that, due to the nature of Pharo, this grammar is somehow artificial because it is not implemented in a specific parser. 
MoTion is implemented as extension methods on existing classes (see also Section *@secImplementation@* ). 
In this grammar, the non-terminals <PharoClass>, <PharodLiteral>, <PharoSymbol>, and <PharoString>, refer to normal elements of Pharo (respectively, a class name, a literal, a symbol and a string).


<Pattern> ::= <LiteralPattern>
    | <PharoClass> <Percentage> '{' <Properties> '}'

<LiteralPattern> ::= <PharoLiteral> 'asMatcher'

<Percentage> ::= '%'
    | '%%'

<Properties> ::= ( <Property> <SpaceShip> <Value> )*

<Property> ::= <PropertyElement>
    | <Traversal>

<SpaceShip> ::= '<=>'
    | '<~=>'

<Value> ::= <PharoSymbol>
    | <Pattern>
    | <NonLinearPattern>
    | <ListPattern>

<PropertyElement> ::= <PharoSymbol>

<Traversal> ::= <PathTraversal>
    | <RecursiveTraversal>

<PathTraversal> ::=  
<PharoSymbol> ( '>' <PathName> )*

<PathName> ::= <PharoString> | '_'

<RecursiveTraversal> ::=  
    <PharoSymbol> '*' ( '>' <PathName> '*' )*

<NonLinearPattern> ::= '#@' <PharoString>

<ListPattern> ::= '{' ( <ListItem> '.' )* '}'

<ListItem> ::= <NonLinearPattern>
    | <PharoLiteral>
    | '\_'
    | '*\_'

#### Pattern operators
@secSyntax

We now explain the semantics of the pattern matching language constructs while showing how they implement the features listed in Section *@secSota@*.

-   <LiteralPatterns> are Pharo literals used as patterns. For example `’A sample text here’ asMatcher` and `1 asMatcher`. Literal patterns match exactly their literal value. This is useful for specifying the value that a property of an object must have.

-   The <SpaceShip> operator tries to match a <Property> (of an object) on the left with a <Value> on the right. Note: the tilde version is a negation, it specifies that the <Property> should not match the <Value>; It is the only way to specify a negation in MoTion. As noted before, it is a polymorphic operator depending on the content in the <Property>. If this is an object, the operator tries to match this object to the <Value>; If it is a collection, the operator tries to match any element of the collection to the <Value>.

-   To define an _object pattern_, one specifies its type using the <PharoClass> followed by the <Percentage> operator like in: `ClassA % {} `. '%' matches direct instances of the class, whereas '%%' matches instances of the class or any of its subclasses.

-   These two operators can express sub-patterns and the properties of the matched object inside the curly braces. Object properties are instance variable accessors. The curly braces act as a conjunction of sub-patterns specifying the values that properties should match. It can be seen as a _Logical matcher_. The following pattern matches an object of class `ClassA`, with a <Property>: `property1`, having the <Value>: `aValue1`, and `property2` having the <Value>: `aValue2`.

```St
ClassA % {
    #'property1' <=> aValue1.
    #'property2' <=> aValue2.
}
```

The sub-patterns could also be more complex (see below, _Structural pattern_). This mechanism contributes to the seamless addition of various properties, in a _declarative_ way.

-   The <Percentage>, combined with the <SpaceShip> operator, also allows to express _Structural pattern_ where a first object is matched, then a second object in one of the properties of the first is matched. One may express a sub-pattern on this second object. For example, the following pattern matches an instance of `ClassA` with `aValue1` in its `property1`, and an instance of `ClassB` in its `property2`. This second object must have `aValue3` in its `property3`.

```St
ClassA % {
    #'property1' <=> aValue1.
    #'property2' <=> ClassB %% {
        #'property3' <=> aValue3.
    }
}
```

-   _Non-Linear pattern_ is obtained using the "`@`" operator followed by a name (for example: `@x`). This allows to store a matched object in the "variable" to reuse it somewhere else in the pattern.

-   _Wildcard_ ("`_`") can be used to indicate a property whose name is not known, when one only cares for its value:
```St
ClassA % {
    #_ <=> aValue.
}
```
This pattern matches an instance of `ClassA` with an unnamed property matching the value `aValue`.

-   The <PathTraversal> operators implement _Path traversal_ by allowing to "chain" multiple properties in a pattern. Such paths help reducing complex pattern's expression, by accessing a chain of objects and their properties:

-   The "`>`" operator implements _Path traversal_ by allowing to "chain" multiple properties in a pattern. Such paths help reducing complex pattern's expression, by accessing a chain of objects and their properties: The following pattern first matches an instance of `ClassA`, then it takes the object in its `property1` and the value in `property2` of this second object. This value should match `aValue`.

```St
ClassA % {
    #'property1>property2' <=> aValue.
}
```
This notation allows expressing in a concise way a path in a graph of objects. The same result could be obtained with the pattern:
```St
ClassA % {
    #'property1' <=> Object %% {
        #'property2' <=> aValue
    }
}
```
Note that the "`>`" operator is also polymorphic. Similarly to "`<=>`", if one of the objects in the path is a collection, the operator will look for an element of this collection that allows to continue the search, that is to say that has a property matching the remaining part of the pattern.

-   MoTion allows to perform _Recursive traversal_ through a "`*`" operator combined with the _Path traversal_ operator "`>`". In a chain of objects, one may know the initial property and the final one, but not know how long the chain of objects is.
```St
ClassA % {
    #'property1>repeatedProp*' <=> aValue.
}
```
This pattern will match first an instance of `ClassA`, then the object in its property `property1` then it will match a chain of objects all having a property `repeatedProp` and one of them containing the value `aValue`. The match ends with this last object.

-   The <RecursiveTraversal> operator may also be combined with a _wildcard_ ("`_`").
```St
ClassA % {
    #'property1>_*>propN' <=> aValue.
}
```
This pattern will match first an instance of `ClassA`, then the object in its property `property1` then a chain of objects with unknown properties ending with an object having a property `propN` with value `aValue`.

-   It is possible to match _Complex lists_ using the <ListePattern> and declaring how the list should look like. Note that this is not the same operator as <Percentage> (see above). This operator allows to express that given elements in a list should match specific patterns.
```St
{#'@x'. #'@x'}
```
This pattern matches a list containing exactly two elements that are the same (use of a named variable).

-   The repetition operator ("`*`") may also be used in a list to indicate an unspecified number of elements.
```St
{#'@x'. #'*_'. #'@x'}
```
This pattern, matches a list with first and last elements equal and of unspecified length (obviously at least 2). Note that `’*_’` is used in list matching whereas `’_*’` is a repeated _wildcard_ used in _Recursive traversal_.

-   To express that one element is part of a collection, MoTion offers a shortcut. To check if the value 5 is part of a collection (contained in the property `someProperty` of an instance of `ClassA`) one can use the pattern:
```St
ClassA % {
    #someProperty <=> {#'*_'. 5. #'*_'}
}
```
But, thanks to the already presented polymorphism, of the <SpaceShip> operator, the same can be expressed with a shortcut:

```St
ClassA % {
    #someProperty<=> 5
}
```
This, however, could also match an instance of `ClassA` with a property `someProperty` containing exactly the value 5 (with no collection).

-   Finally, there is another operator for _Logical matcher_: `orMatches:`. It allows to express a disjunction of two patterns (one or the other match). (Remember that <Percentage> implements a conjunction of patterns within the curly braces.)
```St
ClassA % {
    #someProperty <=> (5 orMatches: 6)
}
```
This pattern matches an instance of `ClassA` with a property `someProperty` matching the value 5 or the value 6.

#### Using MoTion 
@secUsingMotion

First, one gets a "matcher" by calling the `asMatcher` method. 
We showed an example of this at the beginning of Section *@secSyntax@*: "`1 asMatcher`" creates a matcher that only matches the value "1".

Second, a matcher has a `match:` method that allows it to try to match the argument.

The result of `match:` is a `MatchingResult`. 
It includes a boolean property `isMatch` indicating whether the match was successful or not. 
It also has the property `matchingContexts` which is a collection of `MatchingContext` objects. Each of these contexts includes again a boolean field `isMatch` and a dictionary of its `bindings`.

The following creates a matcher that matches anything and binds it to the "foo" symbol (first line). The pattern is run on the string `’text’`. 
The last line will answer `true` as the match was successful.

```St
pattern := #'@foo' asMatcher.
result := pattern match: 'text' .
result isMatch.
```

To get the binding of `foo` in this small example, one would do (`bindings` returns a dictionary and `at:` is the standard method to access an element of a dictionary):

```St
result matchingContexts first
bindings at: 'foo'.
```

This will return the string `’text’`.

Bindings can also be created with the `as:` method. 
It is used to bind the result of a pattern that will be kept in the result's bindings. 
For example, in Listing *@adonisPattern@*, it is used to store the result of the sub-pattern in lines 3 to 7 (the matched FamixJavaInterface).

Finally, to simplify getting the result of the bindings one is mostly interested in, there is a method `collectBindings:` that accepts a collection of (interesting) keys as a parameter and returns their values matched by a pattern. In case there is no match, the return is an empty collection.

```St
pattern := #'@foo' asMatcher.
results := pattern 
    collectBindings: {#foo } 
    for: 'text' .
```

This puts in `results` a collection of dictionaries (here there is only one) with the binding for the `#foo` symbol. 
The result is a collection because there could be several matchings (for example with a disjunction operator). 
The collection holds dictionaries because we could ask for several bindings in the first parameter of the method.

### Implementation Notes 
@secImplementation

MoTion uses the flexibility of Pharo syntax to implement the operators and enable the creation of additional operators or the specialization of existing operators.

For example the "% {}" operator is implemented as a method on `Class` (actually, the method is ‘%‘ and the curly braces are the argument of the method) so that this expression is valid in Pharo:

```St
ClassA % {
    ...
}
```

We saw in the previous section that some operators are polymorphic ("`<=>`" and "`>`"). This is implemented through a polymorphic `#match:withContext:` method (not further described here).

In the following subsections, we propose some examples of implemented extensions, but more details about this implementation can be found on the open source hub of the project. 

In summary the implementation relies on:

-   A class `Matcher` responsible for matching a pattern to a model with the method `match:` (see also Section *@secUsingMotion@*). 
It has 19 subclasses performing some operators (like `%` ) or literals as patterns,...

-   Classes `MatcherResult` and `MatcherContext` that hold the result of a matching. An instance of `MatcherResult` is obtained as the returned value of the `match:` method (see above)

-   Class `MotionPath` to implement the various path features: <PropertyElement> (ie. `#name`), _Wildcard_(ie. `#_`), _Path traversal_(ie. `>`),...

It has six subclasses all implementing a method `resolveFrom:`.

-   Six implementations of a method `asMatcher` added to pre-existing classes Array, Boolean, Class, Number, String, and Symbol. 
They convert a literal or Object to a pattern (ex: 'A sample text here' `asMatcher`).

-   Methods `%` and `%%` implemented in Class to allow expressing _Object matching_(ie. <PharoClass> `% {}`).

-   the <SpaceShip> methods (ie. `<=>` and `<~=>`) added to class `Object`

#### A simple extension

Listing *@adonisPattern@* showed an example of a pattern on a Famix model. 
We actually implemented an extension of MoTion for Famix.

In Famix, the properties of entities can represent:

-   "Famix _properties_" that contain "Famix primitive types" (Numbers, String or Boolean);

-   _associations_ that point to another Famix entity (a FamixJavaMethod _invokes_ multiple other FamixJavaMethods);

-   _composition_ relationships (a FamixJavaClass _contains_ multiple FamixJavaMethods).

Because the properties are meta-described, one can manipulate them programmatically. We therefore experimented with modifying the behavior of the path operator ("`>`") to navigate only _composition_ relationships. We also added another operator to preserve the previous behavior of the path operator.

#### Changing the syntax

Another experiment could be to change the syntax of MoTion to make it easier to understand for novice users. 
For this, we propose to replace the operators with keyword messages: The "% {}" operator could be replaced by the message "`instanceWithProperties:`"; "`<=>`" operator could be replaced by the message "`objectMatches:`", and the `<~=>` operator could be replaced by the message
"`objectDoesNotMatch:`".

We illustrate these changes on the pattern example of Listing *@adonisPattern@*. The result is shown in Listing *@humanReadablePattern@* with the changes highlighted in bold. It's important to emphasize that both patterns are valid and interpreted by MoTion in exactly the same way. We just added "synonym" methods.

```language=St&caption=MoTion operator replaced by Pharo message&label=humanReadablePattern
FamixJavaModel instanceWithProperties: {
 #'allTypes>entities' objectMatches:
  ((FamixJavaInterface instanceWithProperties:{
   #'superInheritances>superclass>name'
   objectMatches: 'Remote' .
   #'isStub' objectDoesNotMatch: true.
 }) as: 'foundInterface')
}
```

The downside of this approach is that we need to put parentheses around the sub-patterns. Here, the "`as:`" message (line 7) could "collide" with the new keyword messages (`objectMatches:` on line 2 and `instanceWithProperties:` on line 3) and be mistaken for a composed keyword message (`objectMatches:as:` or `instanceWithProperties:as:`). This is an issue that did not arise with the use of symbols because of the precedence of binary messages in Pharo. Note also that, instead of the inner parentheses, we could actually have created the `instanceWithProperties:as:` method that would first call `instanceWithProperties:` and then `as:` on its result.

### Use cases 
@secUsecases

We used MoTion in some of our projects and presented it to other people to use in their projects. We report here some of these experiments. We will summarize the lessons learned from these experiments in Section *@secLessonsLearned@*.

#### External dependencies

MoTion was used in a project on external dependencies detection {!citation|ref=Hosr23a!} that deals with polyglot software, developed using several programming languages at the same time. This is the case for example of GWT applications that use Java and XML, or RMI systems where two applications (client and server) must cooperate.

In order to be able to detect dependencies in these projects, we used MoTion to create more generic patterns that could be reused for different frameworks. For example, searching for an XML attribute was used for GWT applications, but could be reused in other cases.

Our running example (Listing *@adonisPattern@*) comes from this experiment. It was already presented and explained in Section *@secPatternExample@*.

We noticed in this work, the use of multiple features of MoTion together for many patterns:

-   structured patterns for complex objects such as `FamixJavaModel % {...}` (line 1) and `FamixJavaInterface % {...}` (line 3);

-   traversal paths expressed in this listing in lines 2 and 4, that allow matching chains of objects;

-   negative search (line 6).

#### Refactoring source code

Our next use case is a developer who used MoTion for a refactoring task over a Java application with a model that contains more than 1.5 million entities.

The problem was to detect all the invocations of method `get` on an object `config` (the receiver) with argument a specific key (`config.get(`*`aKey`*`)`). This needed to be done on a representation of the AST of the method to be able to modify the AST after.

The developer created the pattern in Listing *@reverseEngineeringPattern@* .


```language=St&caption=Reverse engineering pattern&label=reverseEngineeringPattern
FASTJavaMethodEntity % {
 #'children*' <=> FASTJavaMethodInvocation % {
  #'receiver>name' <=> #'config'.
  #name <=> #get.
  #'arguments>primitiveValue' <=> aKey.
 } as: #configInvocation
}
```

The pattern was applied to FAST-Java, a member of the Famix family specializing in modeling Java ASTs. It starts by matching a FASTJavaMethodEntity (ie. a method node) and looks at its children for a FASTJavaMethodInvocation (line 2). Because this invocation could be at any depth in the AST, he used the "`*`" operator (_Recursive traversal_). On the invocations matched, it looks for the receiver's name which should be "config" (line 3). The name of the invocation (method invoked) should be "get" (line 4). The argument of the invocation should be an object with the property "primitiveValue" matching `aKey` (line 5). Here, the key is a parameter that can change for different searches.

We noted in this work:

-   The _Recursive traversal_ which was necessary because the invocation is at different depths in the AST in different methods.

-   The ease of use, the developer was able to work alone after a small presentation of MoTion syntax of only half an hour.

-   The need for "named sub-patterns" that could be reused to compose complex patterns. Actually this feature exists but the developer did not think about it. The solution is simply to put a pattern in a variable that can be reused to build more complex patterns.

As an example Listing *@reverseEngPatternDecoupled@* presents a rewritten version of the pattern represented in Listing *@reverseEngineeringPattern@* (even though there is no sub-pattern reuse there). Variables are highlighted to help read the pattern.

```language=St&caption=Reverse engineering pattern decomposed&label=reverseEngPatternDecoupled
childrenPath := #'children*'.
receiverNamePath := #'receiver>name'.
argsVal := #'arguments>primitiveValue'.

subPattern := FASTJavaMethodInvocation % {
receiverNamePath <=> #'config'.
 #name <=> #get.
argsVal <=> aKey.
} as: #configInvocation.

FASTJavaMethodEntity % {
 childrenPath <=> subPattern.
}
```

#### Backend for other pattern matching

In another work {!citation|ref=Hosr23b!}, we compared MoTion to `RBParseTreeSearcher`. It is a pattern matching language to search over the Pharo AST (and possibly rewrite the AST with `RBParseTreeWriter`).

We compared MoTion to `RBParseTreeSearcher` class, by applying a search over the same Pharo AST, with both matching languages. Listing *@pharoAstMatcher@*, shows the two patterns, used to check if the AST contains a selector `#ifTrue:ifFalse:`.

The patterns in `RBParseTreeSearcher` syntax (line 1) look similar to the original Pharo source code, except that some operators are used to help describe the pattern. Here, we are using the backtick operator (`‘@`) to refer to a list of nodes in the AST. The pattern `‘@receiv` can match multiple nodes that behave as a receiver for the `#ifTrue:ifFalse:` message, and the blocks can contain multiple arguments inside, that are different from each other after naming them `args1` and `args2`.

In MoTion (line 3 to 5), we defined a pattern of type `RBMessageNode`, and used a traversal path to match the selector searched for.

```language=st&caption=Pharo AST matcher&label=pharoAstMatcher
`@receiv ifTrue: [ `@args1 ] ifFalse: [ `@args2 ].
----------------------------------------------------
RBMessageNode % {
    #'selector>value' <=> #ifTrue:ifFalse:
}
```

We noted in this work:

-   With RBParseTreeSearcher, specifying patterns to detect the receiver and the list of arguments inside the blocks is mandatory, while in MoTion, this specification could be skipped as the developer is only interested in knowing if the selector is invoked in this code or not.

-   We found that RBParseTreeSearcher is faster. This should be expected as it is a matching language dedicated to only Pharo ASTs, while MoTion is a generic and can match any object at any depth, implying more computation and thus more time to execute.

-   RBParseTreeSearcher lacks some capabilities, like the ability to express path traversal (see *@tabobjectLanguagesTable@* for the features of this  matching language).

### Lessons learned 
@secLessonsLearned

In this section, we summarized the take-outs of our experiments, both positive and negative.

#### Comparison with pre-existing

We compared the performances of MoTion and RBParseTreeSearcher patterns for Pharo AST search. MoTion was slower. We suppose this comes from the fact that RBParseTreeSearcher is fine tuned for matching Pharo AST nodes. For example it lacks some capabilities that MoTion has and makes the matching more computationally demanding.

We are considering whether it would be possible to compile MoTion patterns to make them more efficient. This is the subject of future work.

We conducted an experiment comparing pattern matching (MoTion) with traditional programming approaches using the reverse engineering example described in Listing *@reverseEngineeringPattern@*. For the traditional programming, we implemented a new class with three methods totaling 30 lines of code. These methods are contained within a single class. To use them, an instance of the class must be created. The results obtained are equivalent to those achieved with the MoTion pattern encapsulation using `as: #configInvocation`.

In summary:

-   The user code is longer, one class, three methods, 30 lines instead of a 7 lines pattern;

-   _Recursive traversal_(`#’children*’` in MoTion) required to implement a recursive method;

-   Searching in the list of arguments (`#’arguments> primitiveValue’ <=>`aKey) required to loop over the values returned by `arguments` to check their `primitiveValue`;

-   The _Non-Linear pattern_(`as: #configInvocation` in MoTion) simplifies collecting the results that can be later retrieved with `#collectBindings: for:`. Traditional programming requires taking care of how results are returned by each method to collect and return them at the end;

-   The class and methods created are very specific to the problem considered and another pattern would require reinventing a new solution with a possibly very different strategy.

#### Most used features

In the experiments reported, we found the following features to be the most used:

- [Object matching] is the main feature used in all patterns. This is due to the fact that we are in an object oriented language and the things to match are objects.

MoTion, however, unlike Tom or Rascal, can work with any object structure and doesn't require its own definition of the classes to express patterns on them.

We worked with many different models (FamixJava, FASTJava, XML-DOM, Pharo AST, mistletoe model) without having to specify anything specific in MoTion other than the patterns themselves.

- [Repeated Search] helped developers to collect all the matches of a pattern. MoTion does not stop after the first match is found, it stops when the leaf is reached. For now, this option seems to be enough for most common uses. However, we set a future target of adding a feature to limit the number of searches, which will be useful for some cases to prevent cyclic looping. A difficult issue will be to find a succinct syntax to express this feature.

- [Traversal Path] is very useful to match nested objects by simply describing the path to reach them in a concise way. This makes the pattern more readable and understandable by the user.

It was used for example in Listing *@adonisPattern@* (line 4) to navigate from an object, to its `superInheritances`, then the `superclass` of this object, and finally the `name` of the last object.

- [Resursive traversal] is very helpful in searching for properties with unknown depth in a tree, or even for unspecified property with a concrete value. It was used for example in Listing *@reverseEngineeringPattern@* (line 2) to find an invocation that was at an unspecified depth in the AST.

There is a risk with this feature of entering an infinite loop if the graph is cyclic. In our example we used the `children` property which is a containment tree and assures us that the search will end.

For future implementations, we are planning to add a limit number for the recursive search like (`*numberOfSearches`) that will prevent it from running forever.

- [Wildcards] not only helped developers express ignored properties, we also discovered another important usage of it. It was used by some developers to express multiple properties having common sub-properties, and the latter are the ones that interest the developers for search.

- [Non-linear pattern] was very beneficial for developers dealing with cross-language applications, as it allowed them to express patterns in testing experiments to match the same value of a property in 2 different languages, like configuration keys defined in an XML file and referred to in a Java method.

On the opposite, complex list patterns were not used explicitly in our experiments. They appear in the "short cut form" in some patterns (eg. Listing *@adonisPattern@*, line 2) when a pattern matches a list and the "`<=>`" operators allow to look for one element of the list.

#### Missing feature

Debugging patterns is a known difficulty in pattern matching.

MoTion can return a false match in cases where patterns were expressed incorrectly (the pattern does not actually match what the user wants). Some help is required for the user to find these mistakes. We started to implement simple solutions, but more needs to be done.

Note, however, that the experiments were related to program analysis, and that may have biased the result based on the features most commonly used. To ensure and quantify well the degree of usefulness of each feature, a bigger study should be conducted, considering the use of MoTion in different contexts.

### Conclusion 
@secConclusion

In this chapter, we introduce MoTion, a new generic object pattern matching language for Pharo Smalltalk. A pattern matching language specifically tailored to match Pharo ASTs is already included in Pharo. MoTion can, however, match ASTs and, more generally, any Pharo object, and it can be used on-the-fly, _i.e.,_: it's not required to redefine artifacts, like object signatures, to use it (opposed to Tom).

In order to create a new object pattern matching language that can offer developers some capabilities like searching among objects with deep depth, defining non-linear patterns, and applying list matching, we have extracted a couple of features known to be adopted by graph and object pattern matching and applied them to MoTion.

We gave an example of MoTion and then presented the syntax in detail. We explained the functionality of each operator and how a match can be applied using different Pharo messages implemented, like `#match:` and `#collectBindings:form:`.

We also presented the implementation of MoTion and how it can be extended if needed. We applied some small modifications to some operators to replace them with more human readable messages. 

In order to prove its feasibility, we presented MoTion to a couple of developers familiar with Pharo, who work in the reverse engineering domain and software analysis for external dependencies extraction. Developers shared their positive experience and requested a couple of features, such as debugging, that we will introduce in our future work. We also compared MoTion syntax with RBParseTreeSearcher to check its feasibility for matching Pharo ASTs. We are planning for the future to change its backend to rely completely on MoTion, as we were able to find some cases where the match is not yielding the correct results at the end.  

Ultimately, we concluded by enumerating the lessons we had learned that had not been taken into account when our matching language was first implemented. For example, developers employed wildcards to indicate anonymous properties as well as the fact that multiple properties occasionally share the same sub-property, the value of which is the one we are interested in matching.