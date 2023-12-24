## Handling Grabouzes with a Zerotroner
@cha:grabouzes

_Authors:_ Prof. T. Tournesol -- Moulinsart Lab, Belgium -- tryphon.tournesol@moulinsart.be and Prof. H. Ochanomizu -- AstroLabs, Japan -- hiro.ochanomizu@astroLabs.jp

##### Abstract
Grabouzes make development tedious and error prone. 
In this article we present how our new Zerotroner handle grabouzes.
We show the challenges posed by grabouzes, present our Zerotroners. 
We present some key applications. In addition, we present the key 
insights of our Zerotroner implementation. Indeed, while modern execution engines offer
excellent execution speed they also offer the possibility to implement efficient zerotroners. 
We finish the articles by showing some result we obtained while applying our Zerotroner
to industrial code. 

### Challenges raised by grabouzes

As shown in Figure *@bluefig@*

![Pharo logo is great.](figures/pharo.png width=50&label=bluefig)

### Presentation

Notice that 
- section titles are not uppercased.
- there is a period at the end of figure captions.

### Implementation insights

```
ZerotronerHandler >> depositron: aCol

	...
```

### Anecdotal use and evidence

As shown in <!cite|key=Tournesol2223!>


### Conclusion

While Pharo is a great language and IDE <!citation|key=Blac09a!>, it does not handle well grabouzes. 
In this chapter we presented how a simple Zerotroner can dramatically improve the situation.