# Full-flow integer gate B1 — rejects absent prepartition/closure

No arithmetic/driver was executed. CaptureFlowEnvelope is source for checked
integer bookkeeping only; it cannot approve matrix/model/runtime work.

For N cells,T cycles,S=2T,DU=8N,DX=30(N+1),DY=DX+DU; K terms,R total rows,r largest,
C addition coefficients,J addition records:

- Raw shape and SDK allowance are EXACT existing ResourcePlan values (SDK3raw+1m
  logical allowance, not allocator/RSS proof).
- Normalized N1241+S1243; normalizer diagnostic640 retains its ticket; affine
  actual allocation reduces unused prefix capacity by640.
- Boundary=(N+1)(30+30DU+900); embedding=DY*DU+DY.
- I=R*DY+R+K*DY+K+C+C/30+4J; V=R(DU+1)+K(DU²+DU+1)+DU²+DU+DY+1.
- W=4rDY+4rDU+4DU²+2DYDU; prefix work P=120DU+3600+60.
- Input original Q=C/30+4J+cache16 and sealed topology Q-base are already jointly
  accounted by (I-Qbase)+V+(W-Qbase-16); do not count nothing or double charge.
- Original cost reused work=(K+1)W; once-per-sample reused work=S*P. No term replay
  for original capture. Normalizer map640 uses and all current charges still count.
- Decoder full-read nominal estimate=ceil(actual input bytes/128)*16, NOT an upper.
  Each successful shortread may provide only1 byte, so worst refill charge upper
  is16*actual input bytes. Existing actual case/batch caps can reject sooner;
  no fixture or codec modification was performed for this bookkeeping repair.
- Writer IO20=cache16+token4, each retained move-only receipt axes4; reader IO28=
  cache16+private expected axes4+token8. IOlease permits no simultaneous writer and
  reader per case. Peak increment at least max(20,28)+4*num_retained_receipts plus
  the B1 role frame20 and all actual other retained metadata/copies.
- Each writer first/new cache generation charges16 BEFORE filling; each decimal/
  f64 token charges4 BEFORE materialization. Reader refill16, headerString/numberToken8
  before materialization; u64 direct scalar parsing uses no separate token array.
- Writer unique successful bytes charged once. Readback does not charge output
  again; metadata observation debits and actual manifests/stdout/arguments/error/
  rosters/chunk headers/READY must be counted separately against frozen limits.
- Actual requested DenseAudit adds its original whole audit allowance; compact
  samples never allocate S dense selectors. All buffered snapshots/copies belong
  in actual live/case/batch charges, not just theoretical final output sizes.

B1 records current live/charges and immutable plan ceilings, and checks the
minimal one-receipt extra IO/frame peak as a NECESSARY condition only. It sets
preplanned_workspace_transfer=false and full_flow_accepted=false ALWAYS because
full leaf/byte/closure/transferred-space admission is not implemented. If current
owners occupy whole liveCeiling, any added IO/frame refuses before output; no
budget increase, scalar replay or disappearing original ticket is allowed.

Required B2 source design PRECONDITIONS (not a certificate minted here): determine
actual role/chunk/receipt counts and maximum scratch/header/manifest buffering
before original cost build; reserve a private same-case capture-workspace receipt
BEFORE allocating that numerical work; reduce the ACTUAL allocated cost/prefix
unused capacity by the same retained capture slots, preserving I+V+W/dense totals;
prove all remaining required work layouts fit. Metadata/tokens/buffers/receipt
lifetimes must be covered by real tickets; every transfer is owner- and case-bound.
The original generic decoder/cost code needs a separately reviewed extension for
that prepartition, then original InitialCostConsumer writes within it.

After cost is already built, its unused double capacity is STILL physically
allocated and ticketed. It cannot be called free space to allocate duplicate
IO arrays; merely having theoretical slack or an integer envelope is insufficient.
A lawful borrowed slice would need actual aliased storage, explicit single-owner
lifetime/disjointness, correct type/alignment and no second allocation. B1 provides
neither this borrow nor a prepartition certificate and therefore REFUSES fullflow.

A B2 manifest gate must also bound actual unique output<=frozen ceiling<=256MiB,
actual metadata<=8MiB, exact typed chunk counts/bytes/coverage/SHA, and complete
independent readback. Source-complete/callback-observed is not byte-complete.
The scientific/physical/controller/stopping/timing/plant/scorer/phase gates remain
separate; backup or this refusal-preserving owner is not Phase5 acceptance.

Final review clarification: planned_existing_source_peak is exactly the PLAN's
upper, never an observed actual peak. current_live is the current ledger snapshot.
The existing cost::used reads normalized native sample.A/B/defect into its factor
work and DOES NOT call affine.withSample; additions stay within each original
term W charge. No records*sampleWork charge is invented. Future once-per-all-sample
export remains separately S*prefixWork. Catalogue visit/reentry/quota failure
latches first refusal and prevents subsequent successful traversal claims.
