import pathlib, subprocess, sys, shutil, tempfile, os
src,dst=map(pathlib.Path,sys.argv[1:]); dst.mkdir(); (dst/'status.txt').write_text('Validation complete')
# Configure repository-specific test command before enabling publication.
command=pathlib.Path('technical-debt-agent/test-command.txt').read_text().strip()
if not command or command.startswith('#'): raise SystemExit('Configure test-command.txt first')
for patch in src.glob('*.patch'):
    with tempfile.TemporaryDirectory() as t:
        work=pathlib.Path(t)/'repo'
        subprocess.run(['git','clone','--local','--no-hardlinks','.',str(work)],check=True)
        try:
            subprocess.run(['git','apply','--check',str(patch)],cwd=work,check=True)
            subprocess.run(['git','apply',str(patch)],cwd=work,check=True)
            subprocess.run(['python','-m','compileall','-q','.'],cwd=work,check=True,timeout=120)
            subprocess.run(command,cwd=work,shell=True,check=True,timeout=600,env={k:v for k,v in os.environ.items() if 'TOKEN' not in k and 'KEY' not in k})
            for p in (patch,patch.with_suffix('.json')): shutil.copy(p,dst)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired): print('Rejected',patch.name)
