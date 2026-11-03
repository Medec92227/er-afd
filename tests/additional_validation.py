"""Casos adicionales separados del histórico 39/1499/20306.

Uso: python3 -m tests.additional_validation --output RUTA_NUEVA.json
Los oráculos usan pertenencia, códigos ASCII e igualdad de bytes, sin regex.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import tempfile

from er_afd import compile_regex
from er_afd.parser import RegexSyntaxError, ResourceLimitError
from .cases import CASES, INVALID_PATTERNS

ROOT = Path(__file__).resolve().parents[1]


def language_cases():
    rows = {}

    def add(pattern, text, expected, family):
        key = (pattern, text)
        if key in rows:
            assert rows[key]['expected'] == expected
            return
        rows[key] = dict(pattern=pattern, text=text, expected=expected, family=family)

    samples = ['', 'aa'] + [chr(i) for i in range(128)]
    for text in samples:
        add(r'[\h00-\h1F\h7F]', text,
            len(text) == 1 and (ord(text) < 32 or ord(text) == 127), 'controles_ascii')
        add(r'[^\h00-\h1F\h7F]', text,
            len(text) == 1 and 32 <= ord(text) <= 126, 'complemento_controles')
        add(r'[^\h00-\h7F]', text, False, 'lenguaje_vacio')
        add(r'([^\h00-\h7F])*', text, text == '', 'cerradura_lenguaje_vacio')
    for length in range(4):
        for chars in product('ab09_\t', repeat=length):
            text = ''.join(chars)
            add(r'[^0-9][^0-9]*', text,
                bool(text) and all(c not in '0123456789' for c in text), 'negativos_compuestos')
    selected = [
        (r'[^0-9][^0-9]*', 'abc_!', True, 'negativos_compuestos'),
        (r'[^0-9][^0-9]*', 'A7', False, 'negativos_compuestos'),
        (r'[^\N\A\a_]', '_', False, 'complemento_macros'),
        (r'[^\N\A\a_]', '\t', True, 'complemento_macros'),
        (r'[^\N\A\a_]', '-', True, 'complemento_macros'),
        (r'[^\N\A\a_]', '5', False, 'complemento_macros'),
        (r'\t', '\t', False, 'escape_generico'),
        (r'\t', 't', True, 'escape_generico'),
        (r'\\\[\]\^\-\|\*\(\)\.', '\\[]^-|*().', True, 'metacaracteres_literales'),
        (r'\\\[\]\^\-\|\*\(\)\.', '\\[]^-|*()X', False, 'metacaracteres_literales'),
        (r'[^\\]*', 'a\\b', False, 'diagonal_excluida'),
        (r'[^\\]*', 'ab/c', True, 'diagonal_excluida'),
        ('[^a][^b]', 'ba', True, 'negativos_por_posicion'),
        ('[^a][^b]', 'aa', False, 'negativos_por_posicion'),
        ('[^a][^b]', 'bb', False, 'negativos_por_posicion'),
        (r'\A\A\h2D\N\N\N', 'GT-007', True, 'codigo_realista'),
        (r'\A\A\h2D\N\N\N', 'gt-007', False, 'codigo_realista'),
        (r'\A\A\h2D\N\N\N', 'GT-07', False, 'codigo_realista'),
        (r'\A\A\h2D\N\N\N', 'GT-00A', False, 'codigo_realista'),
        (r'(\h00|ε)*', '\x00\x00\x00', True, 'nul_y_epsilon'),
        (r'(\h00|ε)*', '\x00a', False, 'nul_y_epsilon'),
    ]
    for row in selected:
        add(*row)
    historical = {(case.pattern, case.text) for case in CASES}
    assert not historical.intersection(rows), 'Un caso reproduce el conjunto histórico.'
    return list(rows.values())


INVALID_NEW = [r'[\h20-\N]', r'a\h4', r'[\h7F-\h00]', r'[^\h80]',
               r'[a-\h00]', r'[^\hG0]', r'(\N|)', '[^😀]', '[a-\\A]']


def audit_source():
    modules = []
    banned_imports, dynamic_calls = [], []
    for path in sorted((ROOT / 'er_afd').glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split('.')[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {'eval', 'exec', '__import__'}:
                    dynamic_calls.append(f'{path.name}:{node.lineno}:{node.func.id}')
        banned_imports += [f'{path.name}:{name}' for name in imports & {'re', 'regex', 'fnmatch'}]
        modules.append({'path':path.relative_to(ROOT).as_posix(),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'imports':sorted(imports)})
    return {'passed':not banned_imports and not dynamic_calls,
            'forbidden_imports':banned_imports,'dynamic_evaluation_calls':dynamic_calls,
            'modules':modules,
            'scope':'Inspección AST de imports y evaluación dinámica; la revisión manual del flujo está en doc/AUDITORIA_IMPLEMENTACION.md.'}


def run_cli_cases():
    rows = []
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')

    def run(label, args, expected, raw=None):
        if raw is not None:
            path = Path(temp) / (label + '.bin')
            path.write_bytes(raw)
            args = [*args, '--file', str(path)]
        result = subprocess.run([sys.executable, '-m', 'er_afd', '--json', *args],
                                cwd=ROOT, env=env, capture_output=True, text=True,
                                encoding='utf-8', timeout=20)
        failures = []
        if result.returncode != expected:
            failures.append(f'retorno {result.returncode}, esperado {expected}')
        try:
            data = json.loads(result.stdout)
            if data.get('exit_code') != expected:
                failures.append('exit_code JSON incoherente')
            if expected == 2:
                if not data.get('error') or 'accepted' in data:
                    failures.append('el error no está diferenciado del rechazo')
            elif data.get('accepted') is not bool(expected):
                failures.append('accepted JSON incoherente')
        except (ValueError, TypeError):
            failures.append('salida JSON inválida')
        if 'Traceback' in result.stdout + result.stderr:
            failures.append('traceback expuesto')
        rows.append({'id':label,'arguments':args if raw is None else args[:-1]+['<archivo_temporal>'],
                     'file_hex':raw.hex() if raw is not None else None,
                     'expected_returncode':expected,'actual_returncode':result.returncode,
                     'passed':not failures,'failures':failures,
                     'stdout':result.stdout,'stderr':result.stderr})

    with tempfile.TemporaryDirectory(prefix='erafd-extra-') as temp:
        pattern = r'\h00\h09\h0D\h0A\h7F'
        run('controles_exactos',[pattern],1,b'\x00\t\r\n\x7f')
        run('cr_ausente',[pattern],0,b'\x00\t\n\x7f')
        run('crlf_exacto',[r'\h0D\h0A'],1,b'\r\n')
        run('crlf_no_normalizado',[r'\h0D\h0A'],0,b'\n')
        run('nul_epsilon_repetido',[r'(\h00|ε)*'],1,b'\x00'*5)
        run('nul_epsilon_rechazo',[r'(\h00|ε)*'],0,b'\x00a')
        run('archivo_vacio_epsilon',['ε'],1,b'')
        run('archivo_vacio_punto',['.'],0,b'')
        for value in [0x80,0xFF]:
            run(f'byte_no_ascii_{value:02X}',['.*'],2,bytes([value]))
        run('utf8_fuera_ascii',['.*'],2,'ñ'.encode('utf-8'))
        run('guion_tras_separador',['--','-a','-a'],1)
        run('escape_t_letra',[r'\t','t'],1)
        run('escape_t_no_tab',[r'\t','\t'],0)
        run('metacaracteres_literales',[r'\\\[\]\^\-\|\*\(\)\.','\\[]^-|*().'],1)
        run('limite_de_estados',['(ab|cd)*e','abe','--max-states','2'],2)
        for i,pattern in enumerate(INVALID_NEW,1):
            run(f'er_invalida_{i:02d}',[pattern,'a'],2)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if platform.system() != 'Linux' or struct.calcsize('P')*8 != 64 or os.getuid() == 0:
        raise SystemExit('Ejecuta esta validación dentro de Linux de 64 bits como usuario regular.')
    if args.output.exists():
        raise SystemExit('El archivo de salida ya existe; elige una ruta nueva.')
    historical_paths=[ROOT/'doc/evidencias/metricas.json',ROOT/'doc/evidencias/linux/20261102T180611Z/metricas_linux.json']
    baseline=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in historical_paths]
    rows = language_cases()
    classify_failures = []
    cached = lru_cache(maxsize=128)(compile_regex)
    confusion = Counter(tp=0,tn=0,fp=0,fn=0)
    for row in rows:
        machine=cached(row['pattern'])
        actual=machine.accepts(row['text'])
        expected=row['expected']
        outputs=[actual,machine.nfa.accepts(row['text']),machine.match(row['text']).accepted]
        row['actual']=actual;row['passed']=all(value==expected for value in outputs)
        confusion['tp' if expected and actual else 'tn' if not expected and not actual else 'fp' if actual else 'fn']+=1
        if not row['passed']:classify_failures.append(row)
    assert not set(INVALID_NEW) & set(INVALID_PATTERNS)
    invalid=[]
    for pattern in INVALID_NEW:
        try:compile_regex(pattern)
        except RegexSyntaxError as error:invalid.append({'pattern':pattern,'passed':True,'error':str(error)})
        else:invalid.append({'pattern':pattern,'passed':False,'error':'No detectó sintaxis inválida'})
    cli=run_cli_cases()
    audit=audit_source()
    after=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in historical_paths]
    historical_preserved=baseline==after
    audit['generated_examples']=[]
    for pattern in ['a','ab','(ab|cd)*e']:
        machine=compile_regex(pattern)
        audit['generated_examples'].append({'pattern':pattern,'nfa_states':machine.nfa.state_count,
            'nfa_transitions':len(machine.nfa.transitions),'dfa_states':machine.dfa.state_count,
            'dfa_transitions':len(machine.dfa.transitions),'dfa_classes':len(machine.dfa.alphabet)})
    passed=not classify_failures and all(r['passed'] for r in invalid+cli) and audit['passed'] and historical_preserved
    report={'completed':True,'passed':passed,'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'environment':{'system':platform.system(),'platform':platform.platform(),'python':platform.python_version(),
                       'machine':platform.machine(),'uid':os.getuid()},
        'historical_metrics_unchanged':baseline,
        'historical_metrics_after':after,'historical_metrics_preserved':historical_preserved,
        'source_audit':audit,
        'additional_language':{'cases':len(rows),'correct':sum(r['passed'] for r in rows),
            'confusion_matrix':dict(confusion),'families':dict(Counter(r['family'] for r in rows)),
            'failures':classify_failures,'cases_detail':rows},
        'additional_invalid_patterns':{'cases':len(invalid),'passed':sum(r['passed'] for r in invalid),'details':invalid},
        'additional_cli':{'cases':len(cli),'passed':sum(r['passed'] for r in cli),'details':cli},
        'note':'Batería adicional independiente; no reemplaza ni se suma al histórico 39/1499/20306. Muestra finita, sin garantía universal.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,ensure_ascii=True,indent=2);stream.write('\n')
    print(json.dumps({'passed':passed,'additional_language_cases':len(rows),
        'invalid_patterns':len(invalid),'cli_cases':len(cli),'source_audit':audit['passed'],
        'output':str(args.output)},ensure_ascii=False))
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
