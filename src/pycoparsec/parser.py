from typing import Generic, TypeVar, Iterator, Callable, Protocol, Optional, List
from itertools import tee, chain
from copy import deepcopy

class SupportsAdd(Protocol):
    def __add__(self, other): ...

S = TypeVar('S') # Token stream type
O = TypeVar('O', bound=SupportsAdd) # Parser output type. Repeated successful parsings call O.__add__. 
S_ = TypeVar('S_')
O_ = TypeVar('O_', bound=SupportsAdd) 

class OutputFactory(Protocol, Generic[S, O]):
    """This is the type that"""
    def __call__(self, __arg: Optional[S] = None) -> O: ...

class FailedParsing(Exception):
    """The parser that raised this exception did not match the current tokens."""
    pass

class DoneParsing(Exception, Generic[S]):
    """The parser that raised this exception reached the end of the input. Eventually, there will be ways to 
    perform early exits or otherwise indicate parsing is finished. That will be what the currently unused 
    ``remaining`` argument will be for."""
    def __init__(self, remaining: Iterator[S] = iter(())):
        self.remaining = [*(tok for tok in remaining)]
        if len(self.remaining) > 0:
            super().__init__(f"There are still tokens left in the stream! Here's what didn't get ingested:\n{self.remaining}")
        else:
            super().__init__()

class Parser(Generic[S, O]):
    """This class implements a parser-combinator style parser on arbitrary None-less iterators.
    Note that the provided Parser interface (``.then``, ``.exactly``, etc.) produce new copies of 
    parser objects instead of performing mutation.
    
    :ivar factory: The function responsible for building the ultimate output of the parser. It should
        either take no argument (indicating a successful empty parse) or one argument (a single value
        parsed from the token stream). Whatever it returns from being called nullarily **must** be the
        identity value with respect to addition on the output type. Built-in Python types already follow
        this convention: e.g, ``int(x) + int() == int(x)`` and ``str(x) + str() == str(x)``.
        In a language with a stronger type-system, this pre-condition could be subbed out for the assertion
        that O is a monoid.
    :ivar matcher: The meat-and-potatoes of the parser. Takes in the next token from the stream, and
        the rest of the token iterator. Gives back either a constructed *output object* or None if the
        parse failed, and the amount of tokens it successfully ingested.
    :ivar choices: A list of other Parsers to try in order if this Parser fails. By default, a newly
        constructed parser always fails, so something like ``Parser().choice(parser1, parser2)`` will
        always defer to ``parser1`` and then ``parser2``.
    """
    MATCHER_TYPE = Callable[[S, Iterator[S]], tuple[Optional[O], int]]

    def __init__(self, factory: OutputFactory[S, O]) -> None:
        self.factory: OutputFactory[S, O] = factory
        self.matcher: MATCHER_TYPE  = lambda tok, rest: None, 0
        self.choices: List["Parser[S, O]"] = []

    def _copy_with(self, matcher: Optional[MATCHER_TYPE] = None, choices: List["Parser[S_, O_]"] = None) -> "Parser[S_, O_]": 
        """Create a new copy of this parser, with the matcher or alternative choices swapped out for new values."""
        out = deepcopy(self)
        if matcher is not None:
            out.matcher = matcher
        if choices is not None:
            out.choices = choices
        return out

    def empty(self) -> "Parser[S, O]":
        """Return a parser which successfully matches no tokens."""
        matcher = lambda tok, rest: (self.factory(), 0)
        return self._copy_with(matcher = matcher)

    def exactly(self, token: S) -> "Parser[S, O]":
        """Match one element of the input stream exactly, then exit."""
        matcher = lambda tok, rest: (self.factory(tok), 1) if tok == token else (None, 0)
        return self._copy_with(matcher = matcher)

    def then(self, parser: "Parser[S, O_]") -> "Parser[S, O]":
        """Chain another parser onto this one, linking their success states together.
        
        Successful parse chains call `__add__` on the output object to append them together. If
        the default behavior of `__add__` does not support the behavior you want, please make a 
        new class which overrides `__add__` and inherits behavior from your desired output type.
        """
        capturedMatcher = self.matcher
        def _matcher(tok, rest):
            print("-- Then! --")
            out, n = capturedMatcher(tok, rest)
            print(n)
            if out is None: return None, 0
            try:
                if n == 0:
                    subout, subN = parser.run(chain([tok], rest))
                elif n >= 1:
                    # We don't manually progres the `rest` iterator here as that's done by the run method.
                    # If .run didn't drive the iterator forward, we'd do something like this here:
                    # for _ in range(n - 1):
                    #     try:
                    #         next(rest)
                    #     except StopIteration:
                    #         raise ValueError("Mismatch between reported token digestion count and real stream token count!")
                    subout, subN = parser.run(rest)
                if subout is None: return None, 0
                return out + subout, n + subN
            except FailedParsing:
                return None, 0
        return self._copy_with(matcher = _matcher)
    
    def optional(self) -> "Parser[S, O]":
        """Greedily match zero or one copies of this parser."""
        return self._copy_with(choices = [*self.choices, self.empty()])

    def many(self) -> "Parser[S, O]":
        """Match many (zero or more) copies of this parser."""
        pass
    
    def some(self) -> "Parser[S, O]":
        """Match some (one or more) copies of this parser."""
        return self.then(self.many())

    def choice(self, choices: List["Parser[S, O]"]) -> "Parser[S, O]":
        """Add a list of alternative Parsers in the case that this Parser fails."""
        return self._copy_with(choices = [*self.choices, *choices])

    def __ror__(self, other: "Parser[S, O]") -> "Parser[S, O]":
        """Cute syntax for supplying alternatives. Allows you to use something like ``(parser1 | parser2).run()``"""
        return self.choice([other])
    def __or__(self, other: "Parser[S, O]") -> "Parser[S, O]":
        """Cute syntax for supplying alternatives. Allows you to use something like ``(parser1 | parser2).run()``"""
        return self.choice([other])

    def run(self, iter: Iterator[S], depth = 0) -> tuple[O, int]:
        """Run this parser. Returns an output value and how many tokens were successfully digested.
        
        :raises FailedParsing: If this parser was not able to parse the input stream in a valid way."""
        def p(*s):
            print("  " * depth, *s)
        ourTee, *tees = tee(iter, len(self.choices) + 1)
        tok = next(ourTee, None)
        p(f"--- Run, tok: {tok}! ---")
        out, n = self.matcher(tok, ourTee)
        if out is not None:
            p(f"Success, out: {out}, n: {n}")
            return out, n
        for teenum, subparser in enumerate(self.choices):
            p("Sub", teenum)
            try:
                subout, subN = subparser.run(tees[teenum], depth + 1)
                if subout is not None: 
                    p(f"Success, subout: {subout}, subN: {subN}")
                    return subout, subN
            except FailedParsing:
                p("Fail")
        p("Exit")
        raise FailedParsing
