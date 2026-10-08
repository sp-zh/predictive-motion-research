"""Read-only exact map identities for extension component audits; no model calls."""
import numpy as np
from audit_public_augmented_sensitivity_root import pack,point,close,blocks,H,DT
from audit_public_physical_derivative_root import need,matrix
CERT='COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1'
def boundary(z,u):
    def side(x,lo,hi):return -1 if x==lo else 1 if x==hi else 0
    return dict(w=[side(x,-.0625,.0625) for x in z['w']],alpha=[side(x,-1,1) for x in u[:7]],s=side(z['s'],0,1),r=side(z['r'],0,.2))
def metadata(m):
    need(m['certificate_name']==CERT and m['certifies_two_sided_admissible_neighborhood'] is False,'explicit extension-only certificate')
    need(m['origin_boundary']==boundary(m['origin'],m['input']) and m['endpoint_boundary']==boundary(m['state'],m['input']),'exact nominal boundary markers')
    for z in (m['origin_boundary'],m['endpoint_boundary']):
        need(all(type(x) is int for key in ('w','alpha') for x in z[key]) and type(z['s']) is int and type(z['r']) is int,'typed boundary markers')
def prefix(case,a):
    """Verify each real certified prefix; never extend a failed nominal trace."""
    count=len(a['substep_maps']);need(count<=len(a['value']['substeps']),'no invented future maps')
    expected=[(ci,k,half) for ci,cell in enumerate(case['cells']) for k in range(1,cell['cycles']+1) for half in (1,2)]
    globalA=np.eye(30);globalB=np.zeros((30,8*len(case['cells'])));orig=case['state'];current=-1;cycle_index=0;cell_index=0;globalmaps=[]
    for si,m in enumerate(a['substep_maps']):
        ci,k,half=expected[si];need((m['cell'],m['cycle'],m['half'])==(ci,k,half),'prefix timing/order');metadata(m)
        if ci!=current:current=ci;cell_initial=orig;priorA=np.eye(30);priorB=np.zeros((30,8))
        if half==1:previousQA=priorA[:7].copy();previousQB=priorB[:7].copy()
        cell=case['cells'][ci];u=np.r_[cell['alpha'],cell['b']]
        matrix(m['A'],30,30);matrix(m['B'],30,8);matrix(m['cell_A'],30,30);matrix(m['cell_B'],30,8)
        A=np.asarray(m['A']);B=np.asarray(m['B']);CA=A@priorA;CB=A@priorB+B
        close(CA,m['cell_A'],1e-12,'independent prefix cell A');close(CB,m['cell_B'],1e-12,'independent prefix cell B');close(pack(m['origin']),pack(orig),0.,'prefix local origin');close(pack(m['cell_origin']),pack(cell_initial),0.,'prefix cell origin');close(m['input'],u,0.,'prefix held input');close(pack(m['state']),pack(point(a['value']['substeps'][si])),0.,'prefix real value endpoint')
        close(m['defect'],pack(m['state'])-A@pack(orig)-B@u,1e-12,'prefix local defect');close(m['cell_defect'],pack(m['state'])-CA@pack(cell_initial)-CB@u,1e-12,'prefix cell defect')
        LA,LB=blocks(1,half);EA,EB=blocks(k,half);close(A[14:],LA,1e-12,'prefix local exact A');close(B[14:],LB,1e-12,'prefix local exact B');close(CA[14:],EA,1e-12,'prefix cell exact A');close(CB[14:],EB,1e-12,'prefix cell exact B')
        close(A[:14,21:28],H*A[:14,14:21],1e-12,'hQ');close(B[:14,:7],H*H*A[:14,14:21],1e-12,'tiny h²Q');close(CA[:14,28:],np.zeros((14,2)),0.,'physical/progress separation');close(CB[:14,7],np.zeros(14),0.,'physical b separation')
        close(CA[:7],previousQA+DT*CA[7:14],1e-12,'prefix semiimplicit q A');close(CB[:7],previousQB+DT*CB[7:14],1e-12,'prefix semiimplicit q B');previousQA=CA[:7].copy();previousQB=CB[:7].copy()
        GA=CA@globalA;GB=CA@globalB;GB[:,8*ci:8*ci+8]+=CB;globalmaps.append((GA,GB))
        if half==2:
            cm=a['cycle_maps'][cycle_index];metadata(cm)
            for key in ('A','B','cell_A','cell_B','defect','cell_defect','input'):close(cm[key],m[key],1e-12,'prefix cycle/half2 '+key)
            for key in ('origin','cell_origin'):close(pack(cm[key]),pack(m[key]),0.,'prefix cycle/half2 '+key)
            close(pack(cm['state']),pack(a['value']['cycle_end_states'][cycle_index]),0.,'prefix complete cycle endpoint');priorA=CA;priorB=CB;orig=cm['state'];cycle_index+=1
            if k==cell['cycles']:
                end=a['cell_maps'][cell_index];metadata(end);close(pack(end['state']),pack(orig),0.,'prefix complete cell endpoint');close(end['input'],u,0.,'prefix cell input');close(end['A'],CA,1e-12,'prefix cell cumulative A');close(end['B'],CB,1e-12,'prefix cell cumulative B');close(pack(end['origin']),pack(cell_initial),0.,'prefix cell-map origin');close(end['defect'],pack(end['state'])-CA@pack(cell_initial)-CB@u,1e-12,'prefix cell-map defect');globalA=GA;globalB=GB;cell_index+=1
    need(len(a['cycle_maps'])==cycle_index and len(a['cell_maps'])==cell_index,'only truly completed prefix cycle/cell maps')
    return globalmaps

def maps(case,a):
    need(a['extension_jacobian_success'] is True and a['value']['success'] is True and a['first_uncertified_substep']==-1 and a['certificate_name']==CERT and a['certifies_two_sided_admissible_neighborhood'] is False,'complete extension-only derivative')
    total=sum(x['cycles'] for x in case['cells']);need(len(a['substep_maps'])==2*total and len(a['cycle_maps'])==total and len(a['cell_maps'])==len(case['cells']),'complete maps')
    return prefix(case,a)
