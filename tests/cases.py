"""Casos de prueba con el resultado esperado escrito a mano."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    pattern: str
    text: str
    expected: bool
    family: str


CASES = [
    Case("a", "a", True, "literal"),
    Case("a", "", False, "literal"),
    Case("a", "aa", False, "fullmatch"),
    Case("a", "ba", False, "fullmatch"),
    Case("ab", "ab", True, "concatenacion"),
    Case("ab", "a", False, "concatenacion"),
    Case("ab", "b", False, "concatenacion"),
    Case("ab", "abc", False, "fullmatch"),
    Case("a|bc", "a", True, "precedencia"),
    Case("a|bc", "bc", True, "precedencia"),
    Case("a|bc", "ac", False, "precedencia"),
    Case("(a|b)c", "ac", True, "parentesis"),
    Case("(a|b)c", "bc", True, "parentesis"),
    Case("(a|b)c", "a", False, "parentesis"),
    Case("a*", "", True, "kleene"),
    Case("a*", "aaaa", True, "kleene"),
    Case("a*", "aaab", False, "kleene"),
    Case("ab*", "a", True, "precedencia"),
    Case("ab*", "abbb", True, "precedencia"),
    Case("ab*", "abab", False, "precedencia"),
    Case("(ab)*", "abab", True, "kleene"),
    Case("(ab)*", "aba", False, "kleene"),
    Case("((a|b)*)*", "abba", True, "epsilon-ciclos"),
    Case("((a|b)*)*", "abc", False, "epsilon-ciclos"),
    Case("ε", "", True, "epsilon"),
    Case("ε", "a", False, "epsilon"),
    Case("aεb", "ab", True, "epsilon"),
    Case("aεb", "a", False, "epsilon"),
    Case("ε|ab", "", True, "epsilon"),
    Case("ε|ab", "ab", True, "epsilon"),
    Case("ε|ab", "a", False, "epsilon"),
    Case("ε*", "", True, "epsilon-ciclos"),
    Case("ε*", "e", False, "epsilon-ciclos"),
    Case("(a|ε)*b", "b", True, "epsilon-ciclos"),
    Case("(a|ε)*b", "aaab", True, "epsilon-ciclos"),
    Case("(a|ε)*b", "aaa", False, "epsilon-ciclos"),
    Case("[abc]", "a", True, "conjunto"),
    Case("[abc]", "d", False, "conjunto"),
    Case("[a-c][0-2]", "b1", True, "rango"),
    Case("[a-c][0-2]", "d1", False, "rango"),
    Case("[a-c][0-2]", "b3", False, "rango"),
    Case("[^abc]", "a", False, "negativo"),
    Case("[^abc]", "z", True, "negativo"),
    Case("[^abc]", "", False, "negativo"),
    Case("[^abc]", "zz", False, "negativo"),
    Case(".", "", False, "punto"),
    Case(".", "aa", False, "punto"),
    Case(".*", "", True, "punto"),
    Case(".*", "A 1!\n", True, "punto"),
    Case("a|.", "b", True, "solapamiento"),
    Case("a|.", "a", True, "solapamiento"),
    Case("a.b|acb", "acb", True, "solapamiento"),
    Case("a.b|acb", "aab", True, "solapamiento"),
    Case("a.b|acb", "ab", False, "solapamiento"),
    Case("[a-c]|[b-d]", "d", True, "solapamiento"),
    Case("[a-c]|[b-d]", "e", False, "solapamiento"),
    Case("[^a]|a", "a", True, "solapamiento"),
    Case("[^a]|a", "b", True, "solapamiento"),
    Case(r"\*\|\(\)\[\]\.\\", "*|()[].\\", True, "escape-literal"),
    Case(r"\p", "p", True, "escape-literal"),
    Case(r"\n", "n", True, "escape-literal"),
    Case(r"\n", "\n", False, "escape-literal"),
    Case(r"hola\ mundo", "hola mundo", True, "espacios"),
    Case("hola mundo", "hola mundo", True, "espacios"),
    Case("hola mundo", "holamundo", False, "espacios"),
    Case(r"\h20\h41", " A", True, "hexadecimal"),
    Case(r"\h7f", "\x7f", True, "hexadecimal"),
    Case(r"\h00", "\x00", True, "hexadecimal"),
    Case(r"\h0A", "\n", True, "hexadecimal"),
    Case(r"\N\N*", "12345", True, "digitos"),
    Case(r"\N\N*", "", False, "digitos"),
    Case(r"\N\N*", "12a", False, "digitos"),
    Case(r"\A\a*", "Guatemala", True, "clases-especiales"),
    Case(r"\A\a*", "guatemala", False, "clases-especiales"),
    Case(r"\z\z*", "AbCd", True, "clases-especiales"),
    Case(r"\z\z*", "Ab3", False, "clases-especiales"),
    Case(r"[\N\A]", "5", True, "escape-en-conjunto"),
    Case(r"[\N\A]", "Z", True, "escape-en-conjunto"),
    Case(r"[\N\A]", "z", False, "escape-en-conjunto"),
    Case(r"[\h41-\h43]", "B", True, "rango-hexadecimal"),
    Case(r"[\h41-\h43]", "D", False, "rango-hexadecimal"),
    Case(r"[\-\]\^]", "-", True, "escape-en-conjunto"),
    Case(r"[\-\]\^]", "]", True, "escape-en-conjunto"),
    Case(r"[\-\]\^]", "^", True, "escape-en-conjunto"),
    Case("a-b", "a-b", True, "guion-fuera-conjunto"),
    Case("[aaa]", "a", True, "duplicados"),
    Case("a|a", "a", True, "duplicados"),
    Case("[0-9][0-9]*", "007", True, "numero"),
    Case("[0-9][0-9]*", "0.7", False, "numero"),
    Case("[a-zA-Z_][a-zA-Z_0-9]*", "var_2026", True, "identificador"),
    Case("[a-zA-Z_][a-zA-Z_0-9]*", "2var", False, "identificador"),
]


# Cada carácter ASCII se contrasta con un oráculo explícito de pertenencia.
CLASS_ORACLES = [
    (".", lambda c: True, "punto-ascii"),
    ("[abc]", lambda c: c in "abc", "conjunto-ascii"),
    ("[^abc]", lambda c: c not in "abc", "negativo-ascii"),
    ("[a-z]", lambda c: "a" <= c <= "z", "rango-ascii"),
    (r"\N", lambda c: "0" <= c <= "9", "digitos-ascii"),
    (r"\A", lambda c: "A" <= c <= "Z", "mayusculas-ascii"),
    (r"\a", lambda c: "a" <= c <= "z", "minusculas-ascii"),
    (r"\z", lambda c: "a" <= c <= "z" or "A" <= c <= "Z", "letras-ascii"),
    ("[a-c]|[b-d]", lambda c: "a" <= c <= "d", "solapamiento-ascii"),
    ("[^a]|a", lambda c: True, "union-complemento-ascii"),
    ("a|.", lambda c: True, "literal-punto-ascii"),
]
for pattern, oracle, family in CLASS_ORACLES:
    for code in range(128):
        char = chr(code)
        CASES.append(Case(pattern, char, oracle(char), family))


INVALID_PATTERNS = [
    "(", ")", "(a", "a)", "a|", "|a", "a||b", "*a", "[", "[abc",
    "[]", "[^]", "[z-a]", "\\", r"\h", r"\h1", r"\hGG", r"\h80",
    "é", "ñ", "[é]", r"[\N-z]", r"[a-\N]",
]


DIFFERENTIAL_PATTERNS = [
    "a", "ab", "a|b", "a*", "(ab)*", "a|bc", "(a|b)c", "(a|b)*abb",
    "ε", "aεb", "ε|ab", "ε*", "(a|ε)*b", "((a|b)*)*", ".", ".*",
    "a|.", "a.b|acb", "[a-c]|[b-d]", "[^a]|a", "[^ab]*c", "[a-c]*",
    r"\N*", r"[\a\N]*", r"\h20|a", "(a|bc)*d",
]
