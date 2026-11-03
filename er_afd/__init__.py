"""ER-AFD: convertidor de expresiones regulares a AFND y AFD."""
from .automata import (CompiledRegex, DFA, NFA, MatchResult, Step,
                       compile_regex, determinize, format_automata, thompson)
from .parser import RegexSyntaxError, ResourceLimitError, parse_regex

__all__ = ["compile_regex", "parse_regex", "thompson", "determinize",
           "CompiledRegex", "DFA", "NFA", "MatchResult", "Step",
           "RegexSyntaxError", "ResourceLimitError", "format_automata"]
__version__ = "1.0.0"
