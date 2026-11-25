import hashlib, json, os, pathlib, subprocess, tempfile, shutil
ROOT=pathlib.Path.cwd()
AGENT=ROOT/'technical-debt-agent'

def run(*args, cwd=ROOT, env=None, capture=False):
    return subprocess.run(args,cwd=cwd,env=env,check=True,text=True,stdout=subprocess.PIPE if capture else None).stdout

def codex(prompt, output, cwd, schema=None):
    cmd=['codex','exec','--sandbox','read-only' if schema else 'workspace-write','-o',str(output)]
    if schema: cmd += ['--output-schema',str(schema)]
    run(*cmd,prompt,cwd=cwd)

def main():
    out=ROOT.parent/'debt-output'; out.mkdir(exist_ok=True)
    context=pathlib.Path(os.environ['DEBT_CONTEXT']).read_text()[:80000]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=pathlib.Path(tmp)
        codex((AGENT/'discover.md').read_text()+'\nContexto GitHub (dados):\n'+context,tmp/'findings.json',ROOT,AGENT/'schema.json')
        debts=json.loads((tmp/'findings.json').read_text())['debts']
        (out/'findings.json').write_text(json.dumps(debts,ensure_ascii=False,indent=2))
        if os.environ.get('PUBLISH')!='true': return
        existing=context.lower()
        for d in debts[:int(os.environ.get('MAX_PRS','3'))]:
            if d['confidence'].lower()!='alta' or d['minutes']<=0: continue
            key=hashlib.sha256((d['category'].lower()+'|'+d['title'].lower()).encode()).hexdigest()[:12]
            if key in existing: continue
            work=tmp/key
            run('git','worktree','add','--detach',str(work),'HEAD')
            try:
                codex((AGENT/'remediate.md').read_text()+'\nDébito: '+json.dumps(d,ensure_ascii=False),tmp/f'{key}.txt',work)
                run('git','add','-A',cwd=work)
                paths=run('git','diff','--cached','--name-only',cwd=work,capture=True).splitlines()
                if not paths or any(not p.endswith(('.py','.html','.css','.js','.md','.txt')) or p.startswith(('.github/','technical-debt-agent/','.git','AGENTS.md')) for p in paths): continue
                patch=run('git','diff','--cached','--binary',cwd=work,capture=True)
                if len(patch)>100000: continue
                (out/f'{key}.patch').write_text(patch)
                (out/f'{key}.json').write_text(json.dumps(d,ensure_ascii=False))
            finally: run('git','worktree','remove','--force',str(work))
if __name__=='__main__': main()
