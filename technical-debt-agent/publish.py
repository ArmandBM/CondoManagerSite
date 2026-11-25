import pathlib, subprocess, sys, os, json, re, tempfile
folder=pathlib.Path(sys.argv[1]); base=os.environ['BASE']; original=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
def run(*a): subprocess.run(a,check=True)
run('git','config','user.name','technical-debt-agent[bot]'); run('git','config','user.email','technical-debt-agent[bot]@users.noreply.github.com')
for patch in sorted(folder.glob('*.patch')):
    key=patch.stem
    if not re.fullmatch('[0-9a-f]{12}',key): continue
    branch='technical-debt/'+key
    if subprocess.check_output(['git','ls-remote','--heads','origin',branch],text=True).strip(): continue
    d=json.loads(patch.with_suffix('.json').read_text())
    run('git','switch','--detach',original); run('git','switch','-c',branch)
    run('git','apply','--index',str(patch))
    paths=subprocess.check_output(['git','diff','--cached','--name-only','-z'],text=True).split('\0')[:-1]
    if not paths or any(not p.endswith(('.py','.html','.css','.js','.md','.txt')) or p.startswith(('.github/','technical-debt-agent/','.git','AGENTS.md')) for p in paths): raise SystemExit('Forbidden patch')
    run('git','commit','-m',f'Technical debt {key}')
    run('git','push','origin',f'HEAD:refs/heads/{branch}')
    body='\n\n'.join(f'**{label}**\n{d[field]}' for label,field in [('Categoria','category'),('Evidências','evidence'),('Contexto','context'),('Impacto e necessidade','impact'),('Solução proposta','solution'),('Riscos','risk'),('Confiança','confidence'),('Função SQALE','formula'),('Teste sugerido','test')])
    body+=f'\n\nEsforço estimado: {d["minutes"]} minutos.\n\nValidação: compilação Python e comando de testes configurado concluídos com sucesso. Revisão humana obrigatória.\n\nID: {key}'
    run('gh','pr','create','--draft','--base',base,'--head',branch,'--title',f'[TD-{key}] '+d['title'][:150],'--body',body)
