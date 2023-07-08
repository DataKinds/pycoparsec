
import pytest
from pycoparsec import Parser

@pytest.fixture
def parse_0_to_9():
    return Parser(str).exactly(1) | Parser(str).exactly(2) | Parser(str).exactly(3) | Parser(str).exactly(4) | Parser(str).exactly(5) | Parser(str).exactly(6) | Parser(str).exactly(7) | Parser(str).exactly(8) | Parser(str).exactly(9) | Parser(str).exactly(0) 

def test_then_1():
    parser = Parser(str).exactly(1).\
        then(Parser(str).exactly(2)).\
        then(Parser(str).exactly(3))
    assert parser.run(d for d in [1,2,3,4]) == ("123", 3)

def test_then_2():
    parser = Parser(str).exactly("h").\
        then(Parser(str).exactly("e")).\
        then(Parser(str).exactly("l")).\
        then(Parser(str).exactly("l")).\
        then(Parser(str).exactly("o"))
    assert parser.run(c for c in "hello, world!") == ("hello", 5)

def test_optional_1():
    parser = Parser(str).exactly("h").\
        then(Parser(str).exactly("e")).\
        then(Parser(str).exactly("l")).\
        then(Parser(str).exactly("l").optional()).\
        then(Parser(str).exactly("o"))
    assert parser.run(c for c in "hello, world!") == ("hello", 5)
    assert parser.run(c for c in "helo, world!") == ("helo", 4)

def test_many_1(parse_0_to_9):
    assert parse_0_to_9.many().run(n for n in range(15)) == "0123456789"

def test_readme_1():
    def string_parser(wanted_string):
        out = Parser(str).exactly(wanted_string[0])
        for c in wanted_string[1:]:
            out = out.then(Parser(str).exactly(c))
        return out
    assert string_parser("Hello").run(c for c in "Hello, world!") == ("Hello", 5)

def test_readme_2(parse_0_to_9):
    assert parse_0_to_9.run(n for n in range(100)) == ("0", 1)

def test_empty():
    assert Parser(str).empty().run(n for n in range(100)) == (str(), 0)