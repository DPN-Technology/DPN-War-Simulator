#!/usr/bin/env python3
"""DPN Security Gate v2 — portable private-repository source security scanner."""
from __future__ import annotations
import argparse, ast, os, re, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEXT_EXT={'.py','.js','.mjs','.cjs','.ts','.tsx','.jsx','.json','.yml','.yaml','.toml','.ini','.cfg','.conf','.env','.md','.txt','.html','.css','.sh','.ps1','.bat','.cmd','.sql'}
CODE_EXT={'.py','.js','.mjs','.cjs','.ts','.tsx','.jsx'}
SKIP=('node_modules/','.venv/','venv/','dist/','build/','vendor/')
TEST=('tests/','test/','fixtures/','examples/')
ENV_TEMPLATES={'.env.example','.env.sample','.env.template'}
SENSITIVE=re.compile(r'(^|/)(\.env|\.env\..+|FIRST_RUN_LOGIN\.txt|id_rsa|id_ed25519|.*\.(?:p12|pfx|key|pem)|(?:vault|master)[^/]*\.key|data/.*\.(?:sqlite|sqlite3|db|enc)|backups?/.*)$',re.I)
KEY_MARKERS=('-----BEGIN '+'PRIVATE KEY-----','-----BEGIN RSA '+'PRIVATE KEY-----','-----BEGIN EC '+'PRIVATE KEY-----','-----BEGIN OPENSSH '+'PRIVATE KEY-----')
TOKENS=(('GitHub token',re.compile(r'\bgh[pousr]_[A-Za-z0-9_]{30,}\b')),('GitHub fine-grained token',re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,}\b')),('AWS access key',re.compile(r'\bAKIA[0-9A-Z]{16}\b')))
CRED=re.compile(r'(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*[\"\']([^\"\']{12,})[\"\']')
PLACEHOLDER=('example','placeholder','changeme','change-me','dummy','sample','test-only','your_')
JS_DIRECT=(('dynamic-eval',re.compile(r'\beval\s*\(')),('dynamic-function',re.compile(r'\bnew\s+Function\s*\(')),('child-process-exec',re.compile(r'\bchild_process\.(?:exec|execSync)\s*\(')))
JS_CP_IMPORT=re.compile(r'(?:require\s*\(\s*[\"\'](?:node:)?child_process[\"\']\s*\)|from\s+[\"\'](?:node:)?child_process[\"\'])')
JS_EXEC=re.compile(r'\b(?:exec|execSync)\b')
@dataclass(frozen=True)
class Finding: path:str; line:int; rule:str; message:str
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True,stderr=subprocess.STDOUT)
def files(): return [p for p in git('ls-files').splitlines() if p and not p.startswith(SKIP)]
def test_path(p): return p.startswith(TEST) or '/tests/' in p or '/fixtures/' in p
def line(text,pos): return text.count('\n',0,pos)+1
def read(p):
    q=ROOT/p
    if q.suffix.lower() not in TEXT_EXT and q.name not in {'Dockerfile','Makefile'}: return None
    try: return q.read_text(encoding='utf-8')
    except (OSError,UnicodeDecodeError): return None
def path_scan(paths):
    out=[]
    for p in paths:
        if Path(p).name.lower() not in ENV_TEMPLATES and SENSITIVE.search(p): out.append(Finding(p,1,'tracked-sensitive-file','sensitive/runtime file must not be tracked'))
    for row in git('ls-files','--stage').splitlines():
        parts=row.split(maxsplit=3)
        if len(parts)!=4 or parts[0]!='120000': continue
        p=parts[3]
        try: target=(ROOT/p).read_text(encoding='utf-8').strip()
        except OSError: continue
        normalized=os.path.normpath(os.path.join(os.path.dirname(p),target))
        if os.path.isabs(target) or normalized=='..' or normalized.startswith('../'): out.append(Finding(p,1,'unsafe-symlink',f'symlink escapes repository: {target}'))
    return out
def text_scan(p,text):
    out=[]
    for marker in KEY_MARKERS:
        pos=text.find(marker)
        if pos>=0: out.append(Finding(p,line(text,pos),'private-key','private key material is tracked'))
    for label,pattern in TOKENS:
        for m in pattern.finditer(text): out.append(Finding(p,line(text,m.start()),'credential-token',f'possible {label} is tracked'))
    if Path(p).suffix.lower() in CODE_EXT and not test_path(p):
        for m in CRED.finditer(text):
            if not any(x in m.group(2).lower() for x in PLACEHOLDER): out.append(Finding(p,line(text,m.start()),'hardcoded-credential',f'hard-coded {m.group(1)}-like value'))
    if Path(p).suffix.lower() in {'.js','.mjs','.cjs','.ts','.tsx','.jsx'} and not test_path(p):
        for rule,pattern in JS_DIRECT:
            for m in pattern.finditer(text): out.append(Finding(p,line(text,m.start()),rule,'dangerous dynamic execution primitive'))
        for m in JS_CP_IMPORT.finditer(text):
            window=text[max(0,m.start()-160):min(len(text),m.end()+160)]
            if JS_EXEC.search(window): out.append(Finding(p,line(text,m.start()),'child-process-exec-import','child_process exec/execSync is prohibited; use spawn/execFile with argument arrays'))
    return out
def dotted(node):
    parts=[]
    while isinstance(node,ast.Attribute): parts.append(node.attr); node=node.value
    if isinstance(node,ast.Name): parts.append(node.id)
    return '.'.join(reversed(parts))
def py_scan(p,text):
    if test_path(p): return []
    try: tree=ast.parse(text,filename=p)
    except SyntaxError: return []
    out=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call): continue
        name=dotted(n.func); ln=getattr(n,'lineno',1)
        if name in {'eval','exec'}: out.append(Finding(p,ln,'dynamic-python-exec',f'{name}() is not allowed in production code'))
        elif name=='os.system': out.append(Finding(p,ln,'os-system','use subprocess with an argument array instead of os.system()'))
        elif name in {'pickle.load','pickle.loads','marshal.load','marshal.loads'}: out.append(Finding(p,ln,'unsafe-deserialization',f'{name}() can load unsafe data'))
        elif name in {'hashlib.md5','hashlib.sha1'}:
            nonsec=any(k.arg=='usedforsecurity' and isinstance(k.value,ast.Constant) and k.value.value is False for k in n.keywords)
            if not nonsec: out.append(Finding(p,ln,'weak-crypto',f'{name}() is prohibited for security/integrity use; use SHA-256+ or mark a compatibility identifier usedforsecurity=False'))
        elif name.startswith('subprocess.') and any(k.arg=='shell' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords): out.append(Finding(p,ln,'subprocess-shell','subprocess shell=True is prohibited'))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--github',action='store_true'); args=ap.parse_args()
    try: paths=files()
    except Exception as e: print(f'DPN Security Gate: unable to enumerate tracked files: {e}',file=sys.stderr); return 2
    findings=path_scan(paths); scanned=0
    for p in paths:
        text=read(p)
        if text is None: continue
        scanned+=1; findings+=text_scan(p,text)
        if p.endswith('.py'): findings+=py_scan(p,text)
    unique=sorted(set(findings),key=lambda f:(f.path,f.line,f.rule,f.message))
    for f in unique:
        if args.github:
            msg=f.message.replace('%','%25').replace('\r','%0D').replace('\n','%0A'); print(f'::error file={f.path},line={f.line},title=DPN Security Gate [{f.rule}]::{msg}')
        else: print(f'{f.path}:{f.line}: [{f.rule}] {f.message}')
    if unique: print(f'DPN Security Gate v2: FAILED — {len(unique)} finding(s) across {scanned} text file(s).'); return 1
    print(f'DPN Security Gate v2: PASS — {scanned} tracked text file(s) scanned; no blocking findings.'); return 0
if __name__=='__main__': raise SystemExit(main())
