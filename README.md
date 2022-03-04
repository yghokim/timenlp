# TimeNLP - Natural Language Time Parser built upon `ctparse` package.
----

This repository is a clone of `ctparse` (https://github.com/comtravo/ctparse), a well established python package that supports natural language time parsing.

Instead of fork, I cloned the repository for easier maintenance.


## Differences from the original `ctparse`
* latent time resolution assumes that the time information is predominantly **past**, rather than the **future**.
* Unlike the original ctparse that supports both German and English, this package focuses on English.
* Expanded rules to support more expressions.