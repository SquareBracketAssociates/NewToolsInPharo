## Define your own refactorings with ReEngine
@cha:refactoring

_Authors:_ B. Sarenac  -- Univ. Novi Sad, Serbia -- sarenac.balsa@proton.me, G. Rakic -- Univ. Novi Sad, Serbia --  and S. Ducasse -- Evref, France -- stephane.ducasse@inria.fr


### Need for a Versatile engine

- Transformations and Refactoring {!citation|ref=Anqu22b!}
- Scripting and Interactive  {!citation|ref=Saren24a!}
- Extensible  {!citation|ref=Saren24b!}





### New Architecture

![ReEngine Architecture. %width=70&anchor=archi](figures/ArchitectureWithChanges2.pdf)

ReEngine's architecture is illustrated in Figure *@fig:rbarch3@*.
- _Driver_ for interactions with the user (interactive mode);
- _Transformation_ for applicability preconditions and modification of the code; 
- _Refactoring_ for expressing behavior-preserving preconditions and extra code changes that would be required to preserve behavior; and 
- _Conditions_ for expressing the preconditions, checking them and register the possible violations.

Here is a typical execution:
- Browser command
- then, a driver creates and configures a refactoring (1),
- then the driver asks the refactoring to check its preconditions (2).
In case of violation, the driver reports to the user (3b).
When preconditions hold, it asks the refactoring to produce changes (3a).
- The driver then previews the changes to the user (4) who can select which ones to apply.
- Finally, the changes are performed on the code (5)


### Transformations and Refactorings


![API. %width=70&anchor=fig:rbarch3](figures/Refactoring-Decorator2.pdf)

### Key APIs

The new API is structured in three layers:

- The first layer is `execute` method (Listing *@lst:execute@*) that will execute complete transformation/refactoring without any user interaction.
This method is used in scripting mode.
- The second layer is `generateChanges` (Listing *@lst:generateChanges@*) and `performChanges` (which are the steps of `execute` method).
This layer is used in interactive mode where the user needs to confirm the changes before performing them on the image.
- The third layer is `checkPreconditions` and `privateTransform` (which are the steps of `generateChanges`).
This layer is used in interactive mode when there is a need for more fine-grained control over execution (e.g. user confirmation is needed for continuation).


Layering the API like this enabled the reuse of the whole execution logic between interactive and scripting modes, and additionally, it enabled the interaction driver to have more fine-grained control over the execution flow.

We will now briefly examine methods from these layers.


#### First layer.
The  `execute` methods of `ReAbstractTransformation`.

```anchor=lst:execute
ReAbstractTransformation >> execute
	self generateChanges.
	self performChanges
```

The `execute` method (Listing *@lst:execute@*) is used during scripting mode, where no user interaction is required.
Developers configure the refactoring and invoke the `execute` method.
The method generates changes by invoking `generateChanges` (line 2) described below.
Changes are objects from the change model and `performChanges` (line 3) applies them to the source code.
As a result, the program is modified. 


#### Second layer. 
The `generateChanges` methods of `ReAbstractTransformation` see Listing *@lst:generateChanges@*.

```anchor=lst:generateChanges
ReAbstractTransformation >> generateChanges
	self checkPreconditions.
	self privateTransform 
```



Creating changes for refactorings and transformations (Listing *@lst:generateChanges@*) is done in two steps: first, check the preconditions (line 2), then generate the code change actions (line 3). 
Each actual refactoring/transformation defines its own preconditions.
They are retrieved by the `checkPreconditions` method and executed.
If a precondition is not satisfied, it raises an error by default.
The error can be caught in interactive mode, to give the user the possibility to correct some parameters.

In the second step, the `privateTransform` method is invoked.
At the level of the superclass `ReAbstractTransformation`, it is an abstract method that is therefore redefined in every refactoring and transformation to implement their own program model transformations.


#### Third layer.
it consists of an API for retrieving preconditions: 

- `preconditions`: to get all preconditions of refactoring or transformation;
- `applicabilityPreconditions`: to get applicability preconditions; and,
- `breakingChangePreconditions`: for breaking changes.
  This last one is implemented only by `ReRefactoring` as transformations do not have breaking changes.

Additionally, some individual reified preconditions (i.e.  instances of an `AbstractCondition` subclass) can be obtained with specific methods (e.g.  `preconditionHasNoReferences`).



### Defining advanced rename instance variables


### Domain specific refactoring

The Pharo virtual machine is written in a subset of Pharo that can be transpiled to C using a VM generator called Slang {!citation|ref=Inga97a!}, {!citation|ref=Mira18a!}. Slang utilizes Pharo to C transpilation: taking Slang code as input, which consists of Pharo code with method annotations  {!citation|ref=Duca16a!} and certain constraints. For example, to be transpiled to C, the VM must not contain polymorphic method definitions, runtime object allocations (new), or exceptions.
Non-local returns are transpilable only when blocks containing them do not get orphan of their outer context, which can occur when block closures are stored in instance variables for future use. By leveraging annotations with different semantics, Slang generates a C file, that once compiled, becomes the Pharo VM {!citation|ref=Poli21a!}, {!citation|ref=Duca22d!}.

In Slang {!citation|ref=Mira18a!}, methods are annotated with compilation directives and type information. An example of this can be seen in Listing *@lst:slang@* which shows the annotation `<var:declareC:>`. 
Certain annotations provide important information such as whether the transpiled method should be inlined or not, should not be transpiled, its return type, or whether the method is an API, ...
Altering these annotations may cause issues during transpilation or with the resulting virtual machine.
Therefore, it is crucial for developers to have the ability to decide whether a pragma should be extracted together with a portion of the method.

```anchor=lst:slang
findFirstInString: aString  inSet: inclusionMap  startingAt: start

    | i stringSize |
    <primitive: ''primitiveFindFirstInString'' module: ''MiscPrimitivePlugin''>
    <var: #aString declareC: ''unsigned char *aString''>
    <var: #inclusionMap  declareC: ''char *inclusionMap''>

    inclusionMap size  = 256 ifTrue: [ ^0 ].

    i := start.
    stringSize := aString size.
    [ i <= stringSize and: [ (inclusionMap at: (aString basicAt: i) + 1) = 0 ] ] whileTrue: [
        i := i + 1 ].

    i > stringSize ifTrue: [ ^0 ].
    ^i
```

Extending the Composite Extract method refactoring involves the following steps:

- First, it is necessary to determine which pragmas need to be moved or copied. This involves adding another method to prepare for the execution hook.
In this proof of concept, we have enabled support for the type pragma `\#type\:declareC\:`.
- Second, the identified pragmas are added to the new method.
To achieve this, an additional transformation has been included in the list of composite transformations (lines 18-23 on Listing *@lst:extract-with-pragmas@*). 

This simple modification allows for the extraction of pragmas. We are currently working on generalizing of this refactoring so that it can support multiple pragmas. However, for the purposes of this proof of concept, we have focused on type pragmas in the Slang language, which is used to develop the Pharo VM.

```caption=Composite Extract Method with Pragmas&anchor=lst:extract-with-pragmas
ReCompositeExtractMethodWithPragmasRefactoring >> buildTransformationFor: newMethodName

	| messageSend |
	messageSend := self messageSendWith: newMethodName.
	^ OrderedCollection new
		  add: (RBAddMethodTransformation
				   model: self model
				   sourceCode: newMethod newSource
				   in: class
				   withProtocol: Protocol unclassified);
		  add: (RBReplaceSubtreeTransformation
				   model: self model
				   replace: sourceCode
				   to: messageSend
				   inMethod: selector
				   inClass: class);
		  addAll: (pragmasToExtract collect: [ :p | 
						ReAddPragmaTransformation
							model: self model 
							addPragma: p
							inMethod: newMethod 
							inClass: class]);
		  add: (ReRemoveUnusedTemporaryVariableRefactoring
				   model: self model
				   inMethod: selector
				   inClass: class name);
		  yourself
```


### Conclusion