import subprocess, sys, os
out=sys.argv[1]
HEAD='''digraph G { rankdir=LR; bgcolor=white; nodesep=0.28; ranksep=0.55; pad=0.12; fontname="Helvetica"; fontsize=12;
node [shape=box style="rounded,filled" fillcolor=white fontname="Helvetica" fontsize=13 height=0.36 margin="0.14,0.05" color="#555555"];
edge [color="#555555" arrowsize=0.7 fontname="Helvetica" fontsize=11];
'''
ROOT='fillcolor="#CFCBFF"'; SEL='fillcolor="#CDEBCF"'; NEW='fillcolor="#FFD9A8" color="#C05A00" penwidth=2'
OLD='fillcolor="#EEEEEE" fontcolor="#888888" color="#999999" style="rounded,filled,dashed"'
ERR='fillcolor="#F8C9C4" color="#B3261E" penwidth=2'; FREE='fillcolor=white fontcolor="#777777" color="#AAAAAA"'
def n(i,l,a): return f'{i} [label="{l}" {a}];\n'
def emit(name,body,head=HEAD):
    p=f'{out}/sources/{name}.dot'; open(p,'w').write(head+body+'}\n')
    subprocess.run(['dot','-Tpng','-Gdpi=200',p,'-o',f'{out}/{name}.png'],check=True)
def blist(items,new=(),title='Selected'):
    r=f'<TR><TD BORDER="0"><B>{title}</B></TD></TR>'
    for x in items:
        c='#FFD9A8' if x in new else '#CDEBCF'
        r+=f'<TR><TD BGCOLOR="{c}">{x}</TD></TR>'
    return f'sel [shape=plain style="" label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="2" CELLPADDING="4" COLOR="#777777">{r}</TABLE>>];\n'
# 1 the diamond
emit('diamond',n('A','A 1.0',ROOT)+n('B','B 1.0','')+n('D','D 2.1','')+n('C2','C 1.2',ERR)+n('C3','C 1.3',ERR)+
 'A->B; B->C2; B->D; D->C3; C2->C3 [dir=none style=dashed color="#B3261E" fontcolor="#B3261E" label="which C?" constraint=false];')
# steps
def step(k,nodes,edges,sel,new):
    b=''.join(n(i,l,a) for i,l,a in nodes)+''.join(f'{e};\n' for e in edges)
    b+=blist(sel,new); last=nodes[-1][0]
    b=b.replace('C2->E','C2->E [weight=5]')
    b+=f'{last}->sel [style=invis weight=0 minlen=2];\n'
    emit(f'step{k}',b)
step(1,[('A','A 1.0',ROOT),('B','B 1.0',NEW)],['A->B'],['A 1.0','B 1.0'],['B 1.0'])
step(2,[('A','A 1.0',ROOT),('B','B 1.0',SEL),('C2','C 1.2',NEW),('D','D 2.1',NEW)],['A->B','B->C2','B->D'],['A 1.0','B 1.0','C 1.2','D 2.1'],['C 1.2','D 2.1'])
step(3,[('A','A 1.0',ROOT),('B','B 1.0',SEL),('C2','C 1.2',SEL),('D','D 2.1',SEL),('E','E 3.5',NEW)],['A->B','B->C2','B->D','C2->E'],['A 1.0','B 1.0','C 1.2','D 2.1','E 3.5'],['E 3.5'])
step(4,[('A','A 1.0',ROOT),('B','B 1.0',SEL),('C2','C 1.2',OLD),('D','D 2.1',SEL),('E','E 3.5',SEL),('C3','C 1.3',NEW)],['A->B','B->C2','B->D','C2->E','D->C3','{rank=same; E; C3}'],['A 1.0','B 1.0','C 1.3','D 2.1','E 3.5'],['C 1.3'])
step(5,[('A','A 1.0',ROOT),('B','B 1.0',SEL),('C2','C 1.2',OLD),('D','D 2.1',SEL),('E','E 3.5',SEL),('C3','C 1.3',SEL),('F','F 4.2',NEW)],['A->B','B->C2','B->D','C2->E','D->C3','{rank=same; E; C3}','C3->F'],['A 1.0','B 1.0','C 1.3','D 2.1','E 3.5','F 4.2'],['F 4.2'])
# released / asked / selected
def cell(v,c): return f'<TD BORDER="1" BGCOLOR="{c}" WIDTH="70">{v}</TD>' if v else '<TD BORDER="0"></TD>'
G,BL,WH='#CDEBCF','#CFE6FF','#FFFFFF'
R=''
for p,vs in [('C',[('C 1.2',BL),('C 1.3',G),('C 1.4',WH)]),('D',[('D 2.1',G),('D 2.2',WH),(None,WH)]),('E',[('E 3.5',G),('E 3.6',WH),(None,WH)]),('F',[('F 4.2',G),(None,WH),(None,WH)])]:
    R+=f'<TR><TD><B>{p}</B></TD>'+''.join(cell(*x) for x in vs)+'</TR>'
leg='<TR><TD></TD></TR><TR><TD BORDER="1" BGCOLOR="%s"></TD><TD COLSPAN="3" ALIGN="LEFT">asked and selected</TD></TR><TR><TD BORDER="1" BGCOLOR="%s"></TD><TD COLSPAN="3" ALIGN="LEFT">asked, below the highest minimum</TD></TR><TR><TD BORDER="1"></TD><TD COLSPAN="3" ALIGN="LEFT">released, asked by nobody</TD></TR>'%(G,BL)
emit('released','t [shape=plain style="" label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="7" CELLPADDING="5" COLOR="#777777">'+R+leg+'</TABLE>>];')
# orphan / cleanup
core=lambda e: n('A','A 1.0',ROOT)+n('B','B 1.0',SEL)+n('C2','C 1.2',OLD)+n('D','D 2.1',SEL)+n('C3','C 1.3',SEL)+n('F','F 4.2',SEL)+n('E','E 3.5',e)
emit('orphan',core(ERR)+'A->B; B->C2 [style=dashed]; B->D; C2->E [style=dashed]; D->C3; C3->F; {rank=same; E; C3}\n')
emit('cleanup',n('A','A 1.0',ROOT)+n('B','B 1.0',SEL)+n('D','D 2.1',SEL)+n('C3','C 1.3',SEL)+n('F','F 4.2',SEL)+n('E','E 3.5',ERR+' fontcolor="#B3261E"')+
 'A->B; B->D; B->C3 [label="asked C 1.2,\\ngets 1.3"]; D->C3; C3->F; {rank=same; E; F}\n E->F [style=invis];')
# major conflict
emit('majors',n('A','A 1.0',ROOT)+n('B','B 1.0','')+n('D','D 2.1','')+n('C1','C 1.2',ERR)+n('C2','C 2.0',ERR)+n('X','Error: two majors of C.\\nNothing is loaded',ERR)+'A->B; B->C1; B->D; D->C2; C1->X [style=dashed]; C2->X [style=dashed];')
# installed
def inst(p,img,res,r): return n(p+'i',f'image: {img}','fillcolor="#EAF4FF"')+n(p+'b','baselines: F 4.2','')+n(p+'m','max','shape=circle')+n(p+'r',f'{res}\\n{r}',SEL)+f'{p}i->{p}m; {p}b->{p}m; {p}m->{p}r;\n'
emit('installed',inst('p','F 4.1','F 4.2','upgraded')+inst('q','F 4.3','F 4.3','kept, never goes down'))
# pipeline
def pipe(p,title,st):
    b=f'subgraph cluster_{p} {{ label="{title}"; labeljust=l; color="#BBBBBB"; style=rounded; margin=12;\n'
    for i,(l,a) in enumerate(st): b+=n(f'{p}{i}',l,a)
    for i in range(len(st)-1): b+=f'{p}{i}->{p}{i+1};\n'
    return b+'}\n'
emit('pipeline',pipe('n','Now',[('resolve\\nchoose one version\\nof every project',NEW),('record\\nbuild the plan',''),('fetch\\ndownload packages',''),('load\\ninto the image','')])+pipe('b','Before',[('record\\nbuild the plan and\\nchoose versions on the way',ERR),('fetch\\ndownload packages',''),('load\\ninto the image','')]))
# reading baselines
emit('reading',pipe('n','Now',[('C repository (git)',''),('sandbox:\\nanonymous BaselineOfC\\nfor v1.2, v1.3, ...',SEL)]).replace('n0->n1;','n0->n1 [label="read from git"]; nimg [label="image\\nuntouched" '+SEL+'];')+pipe('b','Before',[('C repository (git)',''),('working copy',ERR),('image',ERR)]).replace('b0->b1;','b0->b1 [label="checkout v1.3"];').replace('b1->b2;','b1->b2 [label="load BaselineOfC"];'))
# several roots
emit('roots',n('U','load script',ROOT)+n('A','A 1.0',SEL)+n('B','B 1.0',SEL)+n('D','D 2.1',SEL)+n('C2','C 1.2',OLD)+n('C3','C 1.3',OLD)+n('C4','C 1.4',NEW)+
 'U->A; U->C4 [label="second root" color="#C05A00" fontcolor="#C05A00"]; A->B; B->C2; B->D; D->C3;')
# dev
emit('dev',n('U','load script',ROOT)+n('A','A 1.0',SEL)+n('B','B 1.0',SEL)+n('D','D 2.1',SEL)+n('C','C main\\n(dev mode)',NEW)+n('F','dependencies of C,\\nat the versions its baseline asks',SEL)+
 'U->A; U->C [label="dev:" color="#C05A00" fontcolor="#C05A00"]; A->B; B->D; B->C [label="asked 1.2"]; D->C [label="asked 1.3"]; C->F;')
# floating
emit('floating',''.join(n('v'+str(i),l,a) for i,(l,a) in enumerate([('v1.0.0',NEW),('v1.1.0',''),('v1.2.0',''),('v1.3.0',''),('v1.4.0\\nadds group UI','fillcolor="#EAF4FF"'),('v1.5.0\\nhas group UI','fillcolor="#EAF4FF"')]))+
 ''.join(f'v{i}->v{i+1} [dir=none color="#BBBBBB"];' for i in range(5))+
 n('m',"v1.x.x for MVS:\\nthe first of the series,\\nno group UI",ERR)+n('t','v1.x.x as a moving tag:\\nthe latest of the series',SEL)+'m->v0 [constraint=false]; t->v5 [constraint=false]; {rank=same; v0; m} {rank=same; v5; t}')
# toplo
def toplo(name,labels,dev,extra=''):
    f=lambda i: NEW if i in dev else SEL
    b=''.join(n(i,l,f(i) if i!='T' or 'T' in dev else ROOT) for i,l in labels.items())
    emit(name,b+'T->Al; T->B; Al->B; B->Ax; B->X; X->Bm; X->O;'+extra)
base=dict(T='Toplo v0.11.0',Al='Album v0.11.0',B='Bloc v3.0.0',Ax='Alexandrie v2.10.0',X='XML-XMLParser v3.6.3',Bm='BitmapCharacterSet 1.2.7',O='OrderPreservingDictionary v1.6.0')
toplo('toplo',base,())
toplo('toplo-dev',dict(T='Toplo\\ncheckout of the CI',Al='Album v0.11.0',B='Bloc v3.0.0',Ax='Alexandrie',X='XML-XMLParser'),('T',),'') if 0 else None
def ci(p,title,l,dev):
    ids={k:p+k for k in l}; b=f'subgraph cluster_{p} {{ label="{title}"; labeljust=l; color="#BBBBBB"; style=rounded; margin=12;\n'
    for k,v in l.items(): b+=n(ids[k],v,NEW if k in dev else SEL)
    for a,c in [('T','Al'),('T','B'),('Al','B'),('B','Ax'),('B','X')]: b+=f'{p}{a}->{p}{c};\n'
    return b+'}\n'
emit('toplo-ci',ci('i','integration build',dict(T='Toplo\\nCI checkout',Al='Album dev',B='Bloc dev',Ax='Alexandrie dev',X='XMLParser v3.6.3\\n(dev mode, fixed tag)'),('T','Al','B','Ax','X'))+
 ci('d','dev build',dict(T='Toplo\\nCI checkout',Al='Album v0.11.0',B='Bloc v3.0.0',Ax='Alexandrie\\n(version asked)',X='XMLParser\\n(version asked)'),('T',)))
