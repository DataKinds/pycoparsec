from typing import Generic, TypeVar, Iterator, Callable, Protocol, Optional, List
from itertools import tee, chain

class SupportsAdd(Protocol):
    def __add__(self, other): ...

S = TypeVar('S') # Token stream type
O = TypeVar('O', bound=SupportsAdd) # Parser output type. Repeated successful parsings call O.__add__. 

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
    
    :ivar matcher: The meat-and-potatoes of the parser. Takes in the next token from the stream, and
        the rest of the token iterator. Gives back either a constructed *output object* or None if the
        parse failed.
    :ivar choices: A list of other Parsers to try in order if this Parser fails. By default, a newly
        constructed parser always fails, so something like ``Parser().choice(parser1, parser2)`` will
        always defer to ``parser1`` and then ``parser2``.
    """
    def __init__(self) -> None:
        self.matcher: Callable[[S, Iterator[S]], Optional[O]] = lambda tok, rest: None
        self.choices: List["Parser[S, O]"] = []

    def exactly(self, token: S, factory: Callable[[S], O]) -> "Parser[S, O]":
        """Match one element of the input stream exactly, then exit."""
        self.matcher = lambda tok, rest: factory(tok) if tok == token else None
        return self

    def then(self, parser: "Parser[S, O]") -> "Parser[S, O]":
        """Chain another parser onto this one, linking their success states together.
        
        Successful parse chains call `__add__` on the output object to append them together. If
        the default behavior of `__add__` does not support the behavior you want, please make a 
        new class which overrides `__add__` and inherits behavior from your desired output type.
        """
        capturedMatcher = self.matcher
        def _matcher(tok, rest):
            if (out := capturedMatcher(tok, rest)) is None: return None
            try:
                subout = parser.run(rest)
                if subout is None: return None
                return out + subout
            except FailedParsing:
                return None
        self.matcher = _matcher
        return self
    
    def choice(self, choices: List["Parser[S, O]"]) -> "Parser[S, O]":
        """Add a list of alternative Parsers in the case that this Parser fails."""
        self.choices.extend(choices)
        return self

    def __ror__(self, other: "Parser[S, O]") -> "Parser[S, O]":
        """Cute syntax for supplying alternatives. Allows you to use something like ``(parser1 | parser2).run()``"""
        self.choice([other])
        return self
    def __or__(self, other: "Parser[S, O]") -> "Parser[S, O]":
        """Cute syntax for supplying alternatives. Allows you to use something like ``(parser1 | parser2).run()``"""
        self.choice([other])
        return self

    def run(self, iter: Iterator[S]) -> O:
        """Run this parser."""
        ourTee, *tees = tee(iter, len(self.choices) + 1)
        tok = next(ourTee, None)
        if (out := self.matcher(tok, ourTee)) is not None:
            return out
        for teenum, subparser in enumerate(self.choices):
            try:
                subout = subparser.run(tees[teenum])
                if subout is not None: return subout
            except FailedParsing:
                print(f"Failed subparser {teenum}")
        raise FailedParsing
