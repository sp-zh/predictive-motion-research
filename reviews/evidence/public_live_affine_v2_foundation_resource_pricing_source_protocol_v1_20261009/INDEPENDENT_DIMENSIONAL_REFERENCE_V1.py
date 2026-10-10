# Independent dimensional ledger for source-only proposals. No production imports/calls.
from math import prod

CAP={'cells':32,'cycles':375,'terms':32,'rows':8192,'term_rows':256,
     'coefficients':4000000,'records':8192,'matrix':12000000,
     'live':64000000,'charges':512000000,'output':268435456,'metadata':8388608}

def priced_layout(n,t,k,rows,r,coeff,records,mode,encoding):
    samples=t*2;X=(n+1)*30;U=n*8;Y=X+U
    ledger=[]
    def bank(category,name,dimensions=(),copies=1):
        slots=prod(dimensions)*copies
        ledger.append({'category':category,'role':name,'shape':list(dimensions),'copies':copies,'logical_slots':slots})
        return slots
    def subtotal(category):return sum(x['logical_slots'] for x in ledger if x['category']==category)
    # Raw complete map schema: two A/B pairs,five state vectors,input and indices.
    for count,kind in [(samples,'substep_maps'),(t,'cycle_maps'),(n,'cell_maps')]:
        bank('raw',kind+'_A',(count,30,30),2);bank('raw',kind+'_B',(count,30,8),2)
        bank('raw',kind+'_state_fields',(count,30),5);bank('raw',kind+'_input',(count,8))
        bank('raw',kind+'_topology',(count,3))
    # Substep values: four7-vectors;elapsed/s/r;friction force/branches;iteration/kkt/clips;indices.
    bank('raw','substep_q_v_C_w',(samples,7),4);bank('raw','substep_elapsed_s_r',(samples,3))
    bank('raw','substep_force_and_branch',(samples,7),2);bank('raw','substep_iteration_kkt_clips',(samples,4))
    bank('raw','substep_indices',(samples,3))
    bank('raw','cycle_and_cell_and_final_states',(t+n+1,30));bank('raw','cell_alpha_b_cycles',(n,9))
    raw=subtotal('raw')
    bank('sdk','retained_growth_allowance',(raw,),3);bank('sdk','fixed_sdk_planning_reservation',(1000000,))
    # Borrowed complete1238 map coordinates +3/5 topology,not actual duplicated matrices.
    for count,kind,topology in [(n,'cell',3),(samples,'sample',5)]:
        bank('normalized',kind+'_A',(count,30,30));bank('normalized',kind+'_B',(count,30,8))
        bank('normalized',kind+'_state_defect_origin',(count,30),3);bank('normalized',kind+'_input',(count,8))
        bank('normalized',kind+'_topology',(count,topology))
    bank('boundary','o',(n+1,30));bank('boundary','M',(n+1,30,U));bank('boundary','P',(n+1,30,30))
    bank('embedding','T',(Y,U));bank('embedding','t',(Y,))
    bank('input','F',(rows,Y));bank('input','f0',(rows,));bank('input','term_ell',(k,Y));bank('input','term_c0',(k,))
    bank('input','addition_C',(coeff,));bank('input','selected_parent_indices',(coeff//30,));bank('input','record_topology',(records,4))
    # Declared conservative work banks,not additional emitted arrays or FLOP measurements.
    bank('factor_work','full_y_row_work',(r,Y),4);bank('factor_work','control_row_work',(r,U),4)
    bank('factor_work','control_H_work',(U,U),4);bank('factor_work','cross_y_control_work',(Y,U),2)
    bank('sample_work','control_map_work',(30,U),4);bank('sample_work','initial_map_work',(30,30),4)
    bank('sample_work','state_scalar_work',(30,),2)
    bank('condensed','all_Fc',(rows,U));bank('condensed','all_fc',(rows,))
    bank('condensed','term_H',(k,U,U));bank('condensed','term_g',(k,U));bank('condensed','term_c',(k,))
    bank('condensed','canonical_H',(U,U));bank('condensed','canonical_g',(U,));bank('condensed','canonical_ell',(Y,));bank('condensed','canonical_c')
    compact=sum(subtotal(name) for name in ['sdk','normalized','boundary','embedding','input','factor_work','sample_work','condensed'])
    bank('reused_charge','sample_pass_work',(subtotal('sample_work'),),samples)
    bank('reused_charge','original_terms_and_canonical_work',(subtotal('factor_work'),),k+1)
    bank('reused_charge','addition_coefficient_scratch',(coeff,),8)
    bank('reused_charge','two_map_scratch_per_record',(records,30*30+30*8+30),2)
    # Output pricing is a conservative envelope:two priced boundary inventories and evaluation scalar allowances.
    bank('output','raw',(raw,));bank('output','normalized',(subtotal('normalized'),))
    bank('output','priced_boundary_inventories',(subtotal('boundary'),),2)
    bank('output','input_and_used_F',(rows,Y),2);bank('output','input_and_used_f0',(rows,),2)
    bank('output','input_and_used_term_ell',(k,Y),2);bank('output','input_and_used_term_c0',(k,),2)
    bank('output','addition_C',(coeff,));bank('output','addition_parent_indices',(coeff//30,));bank('output','addition_topology',(records,4))
    bank('output','retained_condensed',(subtotal('condensed'),))
    bank('output','direct_and_condensed_evaluation_H',(k+1,U,U),2)
    bank('output','direct_and_condensed_evaluation_g',(k+1,U),2)
    bank('output','priced_evaluation_scalar_allowance',(k+1,2),2)
    if mode==1:
        bank('dense','L',(X,X));bank('dense','E',(X,U));bank('dense','f',(X,));bank('dense','I0',(X,30))
        bank('dense','square_workspace',(X,X),8);bank('dense','RHS_workspace',(X,U+31),6)
        bank('dense','full_solution',(X,U+31));bank('dense','sample_selectors',(samples,30,Y))
        bank('dense','recursive_and_eliminated_sample_o',(samples,30),2)
        bank('dense','recursive_and_eliminated_sample_M',(samples,30,U),2)
        bank('dense','recursive_and_eliminated_sample_P',(samples,30,30),2)
    dense=subtotal('dense');output_slots=subtotal('output')+dense
    return {'dx':X,'du':U,'dy':Y,'raw':raw,'sdk':subtotal('sdk'),'live':compact+dense,
            'charges':compact+subtotal('reused_charge')+dense,'output':output_slots*(8 if encoding==0 else 34)+CAP['metadata'],
            'metadata':CAP['metadata'],'mode':mode,'encoding':encoding,'member_slots':0,'member_charges':0,
            'component_totals':{name:subtotal(name) for name in ['raw','sdk','normalized','boundary','embedding','input','factor_work','sample_work','condensed','reused_charge','output','dense']},
            'dimensional_ledger':ledger}

def admission(n,t,k,rows,r,coeff,records,mode,encoding):
    # Contract domain admission;no use of production implementation or output.
    if not(0<=k<=32 and 0<=rows<=8192 and 0<=r<=256 and rows<=k*r):return 'cost term/row envelope mismatch'
    if r>rows:return 'largest term cannot exceed total rows'
    if k==0 and any([rows,r,coeff,records]):return 'nonempty data with zero terms'
    if coeff>4000000 or records>8192:return 'addition envelope exceeded'
    if coeff%30:return 'addition coefficient rows not dimension30'
    selected=coeff//30
    if not((records==0 and selected==0) or(records>0 and selected>=records and selected<=records*r)):
        return 'addition record/coefficient envelope mismatch'
    dims={'row_matrix':rows*(30*(n+1)+8*n),'Xsquare':(30*(n+1))**2,'YU':(30*(n+1)+8*n)*8*n}
    if max(dims.values())>12000000:return 'individual matrix shape exceeds v2 cap'
    if mode not in [0,1]:return 'unknown capture mode'
    if encoding not in [0,1]:return 'unknown numeric encoding'
    x=priced_layout(n,t,k,rows,r,coeff,records,mode,encoding)
    for field,reason in [('live','whole-request live quota exceeded'),('charges','whole-request cumulative quota exceeded'),('output','whole-request output quota exceeded')]:
        if x[field]>CAP[field]:return reason
    return None
