# pycoparsec

This library is _SLOW_. For large input sequences or large chains of parsers, it will also likely eat an unreasonable amount of memory, even compared to other pure Python parsers like [Parsimonius](https://github.com/erikrose/parsimonious). This is a _PROOF OF CONCEPT_. Do *NOT* use it in production code.

Pycoparsec is my attempt at making a parser combinator style parsing library for Python. The design of the code and of the library takes after [Megaparsec](https://hackage.haskell.org/package/megaparsec-9.4.0/docs/Text-Megaparsec.html), a parser combinator library. Although its feature set more closely aligns with [Attoparsec](https://hackage.haskell.org/package/attoparsec-0.14.4/docs/Data-Attoparsec-ByteString.html) due to the ability to stream tokens into Pycoparsec, and due to Pycoparsec's shitty error reporting (right now it just raises an empty `FailedParsing` object, lol). 

My goals for the project are as follows:

* Type safety, or at least as close to it as Python can get. The whole library is [PEP484](https://peps.python.org/pep-0484/) type hinted. I've opted to keep it 3.8 compatible -- that means no `typing.Self` or subscripting `list`. That can change in the future.
* The ability to ingest arbitrary iterators. This means no peeking ahead at the rest of the tokens, and this means sexy error messages would require me to do hella extra bookkeeping. 
* The ability to construct arbitrary Python objects spat directly out of the parser. It currently does this by folding successive objects with `+`, so if you want to construct objects in a smarter way you'll have to construct your own output classes. There's some funky-ness with how object construction even happens, with the method to construct intermediate output objects embedded directly in the signature of `Parser.exactly`. I am not sure I am satisfied with this yet. No monoids and semigroups means no `mappend` and `<>` to automagically build objects for us.
* Code readability. In a perfect world I would like the main chunk of the code to be a well documented ~500 LoC. You should be able to audit the whole library in an evening, and emerge on the other side with a full understanding of it.

PRs, issues, and contributions welcome. Thanks for reading.
