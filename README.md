# Introduction

The repository contains the codes implemented for the article "Preprocessing Techniques for Qualitative data Clustering via Integer Linear Programming".

Two [Python 3.4](https://www.python.org/download/releases/3.4.0/) classes were implemented:

- RegnierProblem: contains methods to create all the Integer Linear Programming models proposed in the article and run it in the CPLEX solver. This class only works if CPLEX solver is installed in the machine.
- RegnierProblemLP: contains methods to create the models and save then in LP file format (.lp). This class is independent of the CPLEX solver.

Both class has as dependency the [Igraph library](http://igraph.org/). 

## RegnierProblem

The following diagram represents this class. The documentation for each class method can be found at:

![RegnierProblem](readmeFiles/RegnierProblem.png)

## RegnierProblemLP

The following diagram represents this class. The documentation for each class method can be found at:

![RegnierProblemLP](readmeFiles/RegnierProblemLP.png)

# Install



# Usage

There are two Python classes that 
