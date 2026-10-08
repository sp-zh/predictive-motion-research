"""Source-design integer accounting only; no imports of model/numerical libraries."""
import json
NX=30;NU=8;TERMS=32;ROWS=8192;TERM_ROWS=256;ADDITION_COEFFICIENTS=4_000_000
ADDITION_RECORDS=8192;LIVE_CAP=64_000_000;DOC_CAP=256*1024*1024

def plan(N,T,R=ROWS,K=TERMS,C=ADDITION_COEFFICIENTS,records=ADDITION_RECORDS):
    S=2*T;DX=NX*(N+1);DU=NU*N;DY=DX+DU;r=min(TERM_ROWS,R)
    # Conservatively price all numeric slots, including int flags, as 8 bytes.
    # Map: 2*(A900+B240+d30)+3*State30+input8+3 topology ints=2441.
    model_maps=(S+T+N)*2441
    # Substep39 double+13 int slots, state endpoints and explicit cell inputs.
    model_values=S*52+(T+N+1)*30+N*9
    raw=model_maps+model_values
    # SDK/result-growth planning allowance; NOT instrumented allocator proof.
    sdk_reserved=3*raw+1_000_000
    normalized=N*(1238+3)+S*(1238+5)  # prefix/wholecell1170 + nominalorigin30,input8,end30
    boundary=(N+1)*(NX+NX*DU+NX*NX)
    embedding=DY*DU+DY
    inputs=R*DY+R+K*DY+K+C+(C+NX-1)//NX+records*4
    # Reusable term/sum/direct-evaluation workspace; sums stream term rows.
    # Includes products, both gradient/Hessian evaluations, and finite guards.
    factor_work=4*r*DY+4*r*DU+4*DU*DU+2*DY*DU
    sample_work=4*NX*DU+4*NX*NX+2*NX
    condensed=R*(DU+1)+K*(DU*DU+DU+1)+(DU*DU+DU+DY+1)
    compact_buffers=dict(model_result_base=raw,SDKplanning_allowance_only=sdk_reserved,
       normalized_native_blocks=normalized,boundary_o_M_P=boundary,T_and_t=embedding,
       full_factor_and_addition_input=inputs,term_sum_and_direct_evaluation_work=factor_work,
       prefix_stream_work=sample_work,term_and_sum_condensed_capture=condensed)
    # Reservation includes base raw; don't count raw a second time in total.
    compact=sum(v for k,v in compact_buffers.items() if k!='model_result_base')
    dense_audit=dict(L_E_f_initial_selector=DX*DX+DX*DU+DX+DX*NX,
       elimination_workspace=8*DX*DX+6*DX*(DU+NX+1),X_control_offset_initial=DX*(DU+NX+1),
       sample_dense_selectors=S*NX*DY,sample_explicit_recursive_and_eliminated_views=2*S*(NX+NX*DU+NX*NX))
    # Complete compact output: raw result, normalized blocks, both boundary views,
    # F input+used F chunks, additions, full condensed terms and term+canonical-sum evaluations. Canonical sum
    # factor/used_F parts reference term chunks, not another duplicate numeric dump.
    output_slots=raw+normalized+2*boundary+2*R*DY+2*R+2*K*(DY+1)+C+(C+NX-1)//NX+records*4+condensed+2*(K+1)*(DU*DU+DU+2)
    # Fixed upper per numeric scalar32 bytes+2 delimiter bytes and bounded8MiB
    # metadata allowance; actual serialized byte quota remains checked by writer.
    output_bound=34*output_slots+8*1024*1024
    # Conservative tracked scratch-use/copy charges in addition to owned buffers.
    # Raw opaque SDK reservation is logical admission, not SDK malloc telemetry.
    addition_scratch=8*C+2*records*(NX*NX+NX*NU+NX)
    cumulative=compact+S*sample_work+(K+1)*factor_work+addition_scratch
    dense_cumulative=cumulative+sum(dense_audit.values())
    return dict(N=N,total_cycles=T,physical_samples=S,DX=DX,DU=DU,DY=DY,
        raw_map_count=S+T+N,compact_buffers=compact_buffers,
        compact_reserved_numeric_slots=compact,compact_reserved_bytes=8*compact,
        compact_within_proposed_live_cap=compact<=LIVE_CAP,
        cumulative_wrapper_charge_upper=cumulative,cumulative_wrapper_within_512m=cumulative<=512_000_000,
        dense_cumulative_wrapper_charge_upper=dense_cumulative,
        dense_audit_extra=dense_audit,dense_audit_reserved_numeric_slots=compact+sum(dense_audit.values()),
        dense_audit_within_proposed_live_cap=compact+sum(dense_audit.values())<=LIVE_CAP,
        complete_compact_output_numeric_slots=output_slots,complete_compact_json_byte_bound=output_bound,
        complete_compact_json_within_proposed_doc_cap=output_bound<=DOC_CAP,
        complete_compact_binary_byte_bound=8*output_slots+8*1024*1024,
        complete_compact_binary_within_proposed_doc_cap=8*output_slots+8*1024*1024<=DOC_CAP,
        scope='INTEGER_SHAPE_PLAN_NOT_RUNTIME_OR_SDK_ALLOCATOR_PROOF')

if __name__=='__main__':
    cases=[plan(20,200),plan(20,375),plan(32,375),
           plan(20,200,R=1024,K=8,C=200000,records=1000),
           plan(20,375,R=1024,K=8,C=200000,records=1000)]
    print(json.dumps({'purpose':'Prospective shape accounting, no model/matrix/kernel execution',
                     'maximum_envelope_cases':cases[:3],'illustrative_smaller_cost_cases':cases[3:]},indent=2))
