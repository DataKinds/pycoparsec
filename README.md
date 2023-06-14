# pycoparsec

This library is _SLOW_. For large input sequences or large chains of parsers, it will also likely eat an unreasonable amount of memory, even compared to other pure Python parsers like [Parsimonius](https://github.com/erikrose/parsimonious). This is a _PROOF OF CONCEPT_. Do *NOT* use it in production code.

Pycoparsec is my attempt at making a parser combinator style parsing library for Python. The design of the code and of the library takes after [Megaparsec](https://hackage.haskell.org/package/megaparsec-9.4.0/docs/Text-Megaparsec.html), a parser combinator library. Although its feature set more closely aligns with [Attoparsec](https://hackage.haskell.org/package/attoparsec-0.14.4/docs/Data-Attoparsec-ByteString.html) due to the ability to stream tokens into Pycoparsec, and due to Pycoparsec's shitty error reporting (right now it just raises an empty `FailedParsing` object, lol). 

My goals for the project are as follows:

* Type safety, or at least as close to it as Python can get. The whole library is [PEP484](https://peps.python.org/pep-0484/) type hinted. I've opted to keep it 3.8 compatible -- that means no `typing.Self` or subscripting `list`. That can change in the future.
* The ability to ingest arbitrary iterators. This means no peeking ahead at the rest of the tokens, and this means sexy error messages would require me to do hella extra bookkeeping. 
* The ability to construct arbitrary Python objects spat directly out of the parser. It currently does this by folding successive objects with `+`, so if you want to construct objects in a smarter way you'll have to construct your own output classes. There's some funky-ness with how object construction even happens, with the method to construct intermediate output objects embedded directly in the signature of `Parser.exactly`. I am not sure I am satisfied with this yet. No monoids and semigroups means no `mappend` and `<>` to automagically build objects for us.
* Rich test suite. I haven't used `pytest` much, but damnit, I'm gonna learn! Tomorrow.
* Code readability. In a perfect world I would like the main chunk of the code to be a well documented ~500 LoC. You should be able to audit the whole library in an evening, and emerge on the other side with a full understanding of it.

PRs, issues, and contributions welcome. Thanks for reading.

TODO
---
* Some way to easily repeat parsers without calling `Parser.then` over and over again. You can do some silly stuff like `parser.then(parser)`, but at some point you're gonna blow the stack and then nobody's having fun.
* A test suite!

Using the library
---
Everything revolves around the `Parser` object, and that's your building block for everything else. Construct one, then pass a factory to `Parser.exactly` or combine it with other parsers with `Parser.choice` or `Parser.then`. A parser that didn't have `Parser.exactly` called will always fail, and will either end the chain it is in or proceed to the next alternative. It is dead simple -- the rest is up to you. Here's a fun recipe:

```py
from pycoparsec import Parser

def string_parser(wanted_string):
    out = Parser().exactly(wanted_string[0], str)
    for c in wanted_string[1:]:
        out.then(Parser().exactly(c, str))
    return out

string_parser("Hello").run(c for c in "Hello, world!") # => "Hello"
```

Or maybe you're more _alternative_?

```py
from pycoparsec import Parser

only_accept_0_to_9 = Parser().exactly(1, str) | Parser().exactly(2, str) | Parser().exactly(3, str) | Parser().exactly(4, str) | Parser().exactly(5, str) | Parser().exactly(6, str) | Parser().exactly(7, str) | Parser().exactly(8, str) | Parser().exactly(9, str) | Parser().exactly(0, str) 

only_accept_0_to_9.run(n for n in range(100)) # => 0
```

Building the docs, running the tests, you know...
---
This package is built using [Hatch](https://hatch.pypa.io/latest/). This project was partly an excuse to try Hatch, so I've used it to the highest degree possible. Type `hatch env show` to list all of the goodies available to you. If you want to run one of the listed scripts, the syntax is `hatch run <ENV NAME>:<SCRIPT NAME>`. So for example, to open the docs the command is `hatch run docs:open`, which automatically builds them and calls `xdg-open` on the index. 