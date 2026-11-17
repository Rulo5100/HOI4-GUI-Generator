import re,glob,os
names={}
for f in glob.glob('localisation/**/*state*names*english*.yml',recursive=True)+glob.glob('localisation/**/*state*english*.yml',recursive=True):
    for l in open(f,encoding='utf-8-sig',errors='ignore'):
        m=re.match(r'\s*(STATE_\d+):\d*\s*"([^"]*)"',l)
        if m and m.group(1) not in names: names[m.group(1)]=m.group(2)
for f in sorted(glob.glob('history/states/*.txt')):
    t=open(f,encoding='utf-8-sig',errors='ignore').read()
    t2=re.sub(r'#.*','',t)
    if not re.search(r'owner\s*=\s*MAN\b',t2): continue
    sid=re.search(r'\bid\s*=\s*(\d+)',t2).group(1)
    res=re.search(r'resources\s*=\s*\{([^}]*)\}',t2)
    b=re.search(r'buildings\s*=\s*\{(.*)',t2,re.S)
    bs=b.group(1)[:600] if b else ''
    def bl(k):
        m=re.search(r'\b'+k+r'\s*=\s*(\d+)',bs); return m.group(1) if m else '0'
    cat=re.search(r'state_category\s*=\s*(\w+)',t2).group(1)
    prov=re.search(r'provinces\s*=\s*\{([^}]*)\}',t2).group(1).split()
    print(sid,names.get('STATE_'+sid,'?'),cat,'mp',re.search(r'manpower\s*=\s*(\d+)',t2).group(1),'inf',bl('infrastructure'),'civ',bl('industrial_complex'),'mil',bl('arms_factory'),'ref',bl('synthetic_refinery'),'dock',bl('dockyard'),'res',' '.join(res.group(1).split()) if res else '-','cores',' '.join(re.findall(r'add_core_of\s*=\s*(\w+)',t2)),'nprov',len(prov))
