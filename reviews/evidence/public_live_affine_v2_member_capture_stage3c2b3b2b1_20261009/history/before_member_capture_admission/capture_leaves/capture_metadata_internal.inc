  // Included inside the genuine private factory, never a standalone executable.
  static void utf8(std::string_view s){
    need(s.size()<=ResourcePolicyV2::metadata_bytes,"borrowed metadata string exceeds fixed cap");
    for(std::size_t i=0;i<s.size();){unsigned char c=static_cast<unsigned char>(s[i++]);if(c<128)continue;
      Count n=0,code=0,minimum=0;if(c>=0xc2&&c<=0xdf){n=1;code=c&31;minimum=0x80;}
      else if(c>=0xe0&&c<=0xef){n=2;code=c&15;minimum=0x800;}
      else if(c>=0xf0&&c<=0xf4){n=3;code=c&7;minimum=0x10000;}else throw std::invalid_argument("invalid metadata UTF8 lead");
      need(n<=s.size()-i,"truncated metadata UTF8");for(Count j=0;j<n;++j){c=static_cast<unsigned char>(s[i++]);need((c&0xc0)==0x80,"invalid metadata UTF8 continuation");code=(code<<6)|(c&63);}
      need(code>=minimum&&code<=0x10ffff&&!(code>=0xd800&&code<=0xdfff),"noncanonical metadata UTF8 scalar");
    }
  }
  static void evidencePoison(CaptureLeafState& p,const char* why) noexcept{p.rejectEvidence(why);if(!p.status.closed&&!p.status.refused)p.reject(why);}
  static void evidenceCheck(const std::shared_ptr<CaptureLeafState>& p,Count generation){
    try{need(p&&p->evidence_active&&p->evidence_generation==generation,"evidence view outside borrowed generation");p->evidenceHealthy();}
    catch(const std::exception& e){if(p)evidencePoison(*p,e.what());throw;}catch(...){if(p)evidencePoison(*p,"NONSTANDARD_EVIDENCE_VIEW_FAILURE");throw;}
  }
  static OwnedReservation evidenceFrame(CaptureLeafState& p,Count slots){p.evidenceHealthy();need((!p.manifest_active||p.manifest_internal)&&p.owner&&p.status.attached&&!p.evidence_active&&!p.string_active&&!p.original_active&&!p.sample_active&&!p.leaf_active&&!p.forensic_active,"evidence owner absent/reentry");return p.budget.reserve(slots);}
  struct EvidenceGuard {
    CaptureLeafState& p;OwnedReservation frame;
    EvidenceGuard(CaptureLeafState& owner,Count slots):p(owner),frame(evidenceFrame(p,slots)){
      p.evidenceHealthy();need((!p.manifest_active||p.manifest_internal)&&p.owner&&p.status.attached&&!p.evidence_active&&!p.string_active&&!p.original_active&&!p.sample_active&&!p.leaf_active&&!p.forensic_active,"evidence owner absent/reentry");p.budget.chargeScratchOrCopy(slots);p.evidence_active=true;
    }
    ~EvidenceGuard(){p.string_active=false;p.evidence_active=false;}
  };
  static bool keyLess(CaptureLeafState& p,const BoundLeafAttempt& x,const BoundLeafAttempt& y){p.budget.chargeScratchOrCopy(20);if(x.role_!=y.role_)return x.role_<y.role_;if(x.primary_!=y.primary_)return x.primary_<y.primary_;return x.secondary_<y.secondary_;}
  static bool keyLessQuery(CaptureLeafState& p,const BoundLeafAttempt& x,LeafKey y){p.budget.chargeScratchOrCopy(20);if(x.role_!=y.role)return x.role_<y.role;if(x.primary_!=y.primary)return x.primary_<y.primary;return x.secondary_<y.secondary;}
  static LeafKey keyOf(const BoundLeafAttempt& a){return {a.role_,a.primary_,a.secondary_};}
  static void orderedAttempts(std::shared_ptr<CaptureLeafState> p){
    if(p->attempts_sorted)return;
    // Separate40-frame scope ends before metadata40 or coverage20/catalogue20.
    EvidenceGuard guard(*p,40);const Count n=p->attempts.size();need(n<=p->partition->status.receipt_limit,"private attempt roster exceeds admitted limit");
    auto swap=[&](Count i,Count j){if(i==j)return;p->budget.chargeScratchOrCopy(120);
      BoundLeafAttempt held=std::move(p->attempts[i]);p->attempts[i]=std::move(p->attempts[j]);p->attempts[j]=std::move(held);
    };
    auto sift=[&](Count root,Count end){while(root<end/2){const Count left=add(mul(root,2),1);Count child=left;
      if(add(left,1)<end&&keyLess(*p,p->attempts[left],p->attempts[left+1]))child=left+1;
      if(!keyLess(*p,p->attempts[root],p->attempts[child]))break;swap(root,child);root=child;
    }};
    for(Count start=n/2;start>0;--start)sift(start-1,n);
    for(Count end=n;end>1;--end){swap(0,end-1);sift(0,end-1);}
    for(Count i=1;i<n;++i){p->budget.chargeScratchOrCopy(20);const auto x=keyOf(p->attempts[i-1]),y=keyOf(p->attempts[i]);need(x.role!=y.role||x.primary!=y.primary||x.secondary!=y.secondary,"duplicate/overlapping private full-key attempts");}
    p->evidenceHealthy();p->attempts_sorted=true;
  }
  static const BoundLeafAttempt* lookup(CaptureLeafState& p,LeafKey key){
    need(p.attempts_sorted,"private ordered lookup not prepared");Count lo=0,hi=p.attempts.size();
    while(lo<hi){const Count mid=lo+(hi-lo)/2;if(keyLessQuery(p,p.attempts[mid],key))lo=mid+1;else hi=mid;}
    if(lo==p.attempts.size())return nullptr;p.budget.chargeScratchOrCopy(20);const auto& a=p.attempts[lo];const auto actual=keyOf(a);return actual.role==key.role&&actual.primary==key.primary&&actual.secondary==key.secondary?&a:nullptr;
  }
  static const char* storageTraversal(R role){
    switch(role){case R::RawFinalState:case R::RawCellState:case R::RawCycleState:case R::RawMapOrigin:case R::RawMapCellOrigin:case R::RawMapEndpoint:return "actual-q/v/C/w-lengths-then-s/r";
      case R::RawSubstepPhysical:return "actual-q/v/C/w-lengths";
      case R::RawSubstepValueIndicesAggregate:return "actual-value-substep/cell-cycle-half-separate-from-map-indices";
      default:return "row-major";}
  }
  static void bindReference(CaptureLeafState& p,ReferenceFact& f){
    // Never accepts a caller record. Only same-session private paired attempts.
    const auto* actual=lookup(p,f.target);if(actual){const auto& a=*actual;
      need(a.source_origin_==p.source_origin&&a.cost_origin_==p.actual_cost_origin&&a.partition_==p.partition&&a.generation_>0,"private reference foreign origin/generation");
      const auto& r=a.write_.record;need(r.spec.kind==f.kind,"reference exact scalar type mismatch");
      need(r.spec.dimensions.size()==f.rank&&r.count==f.source_count,"reference actual rank/count mismatch");
      for(Count k=0;k<f.rank;++k)need(r.spec.dimensions[k]==f.dimensions[k],"reference actual dimensions mismatch");
      need(f.offset<=r.count&&f.count<=r.count-f.offset,"reference outside full source range");
      need(!f.requires_original_scope||a.original_scope_,"reference lacks ORIGINAL callback provenance");
      need(!f.requires_sample_scope||a.sample_scope_,"reference lacks actual once-sample provenance");
      if(f.requires_sample_scope)need(a.sample_cell_==f.cell&&a.sample_tick_==f.tick&&a.sample_cycle_==f.cycle&&a.sample_half_==f.half,"sample reference provenance mismatch");
      f.paired_verified=f.source_valid&&p.partition->status.applied&&!p.partition->status.refused&&p.budget.sameCase(p.partition->budget)&&!p.status.closed&&!p.status.refused&&p.owner->genuineSource().hasCompleteCost()&&
        a.write_.closedChunk()&&a.readback_&&a.readback_->exact_readback&&!a.readback_->observation.refused&&!a.mismatch_&&a.computed_state_==DefinedComputedState::ComputedOriginal;
    }
    // A paired file check is not reconstruction proof, even for complete ranges.
    f.reconstruction_verified=false;
  }
  static ReferenceFact reference(ReferenceUse use,Count index,Count part,R role,Count first,Count second,std::initializer_list<Count> shape,bool valid){
    ReferenceFact f;
    if(role==R::RawMapIndices||role==R::CachedMetadataIndices||role==R::CachedMetadataDimensions||role==R::ChosenInitialKind||role==R::RawSubstepValueIndicesAggregate||(role==R::RawCellControl&&second==1))f.kind=ChunkScalarKind::I64;
    else if(role==R::CostAdditionRows||role==R::CostAdditionSampleIndex||role==R::ActualBoundaryCounters)f.kind=ChunkScalarKind::U64;
    f.use=use;f.index=index;f.part=part;f.target={role,first,second};f.rank=shape.size();need(f.rank<=4,"reference rank cap");Count n=1,k=0;
    for(Count d:shape){f.dimensions[k++]=d;n=mul(n,d);}f.count=f.source_count=n;f.source_valid=valid;return f;
  }
  static void metadata(std::shared_ptr<CaptureLeafState> p,const MetadataConsumer& caller){
    try{orderedAttempts(p);EvidenceGuard guard(*p,40);const auto sink=caller;p->evidenceHealthy();need(static_cast<bool>(sink),"empty frozen metadata visitor");
      auto emit=[&](MetadataFact f){p->evidenceHealthy();p->budget.chargeScratchOrCopy(40);utf8(f.text);utf8(f.family);utf8(f.field);
        MetadataBinding b{p,std::move(f),++p->evidence_generation};const MetadataLeafView view(&b);sink(view);p->evidenceHealthy();};
      auto text=[&](const char* family,const char* field,std::string_view s,Count i=0,Count j=0){MetadataFact f;f.family=family;f.field=field;f.index=i;f.subindex=j;f.kind=MetadataKind::Utf8;f.text=s;emit(f);};
      auto u=[&](const char* family,const char* field,Count value,Count i=0,Count j=0){MetadataFact f;f.family=family;f.field=field;f.index=i;f.subindex=j;f.kind=MetadataKind::U64;f.unsigned_value=value;
        if(p->manifest_active&&p->manifest_internal&&p->manifest&&std::string_view(family)=="quota"){const auto& q=p->manifest->snapshot_;
          const std::string_view key=field;if(key=="current_live_slots")f.unsigned_value=q.live;else if(key=="current_cumulative_charges")f.unsigned_value=q.charges;else if(key=="actual_metadata_bytes_so_far")f.unsigned_value=q.metadata_bytes;else if(key=="actual_unique_output_bytes_so_far")f.unsigned_value=q.output_bytes;else if(key=="live_ceiling")f.unsigned_value=q.live_ceiling;else if(key=="charge_ceiling")f.unsigned_value=q.charge_ceiling;else if(key=="output_ceiling")f.unsigned_value=q.output_ceiling;else if(key=="metadata_ceiling")f.unsigned_value=q.metadata_ceiling;
        }emit(f);};
      auto integer=[&](const char* family,const char* field,std::int64_t value,Count i=0){MetadataFact f;f.family=family;f.field=field;f.index=i;f.kind=MetadataKind::I64;f.signed_value=value;emit(f);};
      auto boolean=[&](const char* family,const char* field,bool value,Count i=0){MetadataFact f;f.family=family;f.field=field;f.index=i;f.kind=MetadataKind::Boolean;f.boolean_value=value;emit(f);};
      auto missing=[&](const char* family,const char* field,const char* why,Count i=0,Count j=0){MetadataFact f;f.family=family;f.field=field;f.index=i;f.subindex=j;f.kind=MetadataKind::Missing;f.text=why;emit(f);};
      auto file=[&](const char* family,const FileIdentity& identity,Count i=0){text(family,"path",identity.path,i);text(family,"sha256",identity.sha256,i);u(family,"bytes",identity.bytes,i);};
      auto numeric=[&](const char* family,const char* field,R role,Count first,Count second,std::initializer_list<Count> shape,bool valid,Count index=0,Count subindex=0){MetadataFact f;f.family=family;f.field=field;f.index=index;f.subindex=subindex;f.kind=MetadataKind::NumericReference;f.reference=reference(ReferenceUse::NumericMetadata,index,0,role,first,second,shape,valid);bindReference(*p,f.reference);emit(f);};
      const auto& decoded=p->owner->genuineSource();const auto& a=decoded.originalAssembly();const auto& norm=a.originalNormalization();const auto& forecast=norm.originalForecast();const auto* raw=forecast.originalResult();
      need(a.captureOriginToken()==p->source_origin,"metadata source origin changed");const bool valid=decoded.hasCompleteCost()&&!p->status.refused&&!p->status.closed;
      const auto& plan=a.capturePlan();const auto& mesh=forecast.mesh();const auto& context=forecast.actualContext();const auto& profile=forecast.verifiedMetadata();
      text("provenance","source_kind","LiveActual");text("profile","pinocchio_version",profile.pinocchio_version);text("profile","units",forecast.verifiedUnits());text("profile","certificate",forecast.verifiedCertificateName());
      u("profile","joint_names_count",profile.joint_names.size());u("profile","frame_names_count",profile.frame_names.size());
      for(Count k=0;k<profile.joint_names.size();++k)text("profile","joint_name",profile.joint_names[k],k);
      for(Count k=0;k<profile.frame_names.size();++k)text("profile","frame_name",profile.frame_names[k],k);
      integer("profile","nq",profile.nq);integer("profile","nv",profile.nv);
      numeric("profile","nq_nv",R::CachedMetadataDimensions,0,0,{2},valid);
      Count k=0;for(const auto* v:{&profile.masses,&profile.armature,&profile.gravity,&profile.R,&profile.B,&profile.damping}){numeric("profile","vector",R::CachedMetadataVector,k,0,{size(v->size())},valid,k);++k;}
      k=0;for(const auto* v:{&profile.idx_q,&profile.idx_v,&profile.joint_nq,&profile.joint_nv}){numeric("profile","indices",R::CachedMetadataIndices,k,0,{v->size()},valid,k);++k;}
      file("producer",forecast.currentProducerIdentity());file("review",forecast.reviewRecordIdentity());file("protocol",forecast.protocolIdentity());
      const auto& files=forecast.verifiedFiles();u("artifacts","count",files.size());for(Count i=0;i<files.size();++i){text("artifacts","role",forecast.verifiedArtifactRole(i),i);file("artifacts",files[i],i);}
      const auto& libraries=forecast.verifiedLoadedLibraries();u("loaded_dso","count",libraries.size());for(Count i=0;i<libraries.size();++i)file("loaded_dso",libraries[i],i);
      file("constants",context.ranges().constantsIdentity());text("invocation","opaque_sha256",forecast.invocationSha256());file("cost_input",decoded.requestedArtifact());text("cost_input","bound_semantic_sha256",p->partition->semantic_sha);
      text("execution","reviewed_attempt_claim_path",forecast.reviewedAttemptClaimPath());const auto attempts=forecast.releaseAttemptFacts();
      u("execution","prepare_attempts",attempts.prepare);u("execution","open_attempts",attempts.open);u("execution","forecast_attempts",attempts.forecast);
      u("execution","constructor_attempts",attempts.constructor);u("execution","metadata_attempts",attempts.metadata);u("execution","rollout_attempts",attempts.rollout);
      for(const char* field:{"arguments","process_paths","stdout","stderr","exit","actual_claim_identity","source_closure_members","sdk_file_members","original_open_error_record"})missing("execution",field,"NOT_RETAINED_NEEDS_VERSIONED_REVIEWED_EXECUTION_ENVELOPE");
      text("context","observation_id",context.observationId());text("context","transaction_id",context.transactionId());
      numeric("context","actual_initial",R::ActualContextInitial,0,0,{30},valid);numeric("context","previous_control",R::PreviousControlHistory,0,0,{8},valid);
      numeric("context","boundary_counters",R::ActualBoundaryCounters,0,0,{2},valid);
      u("context","completed_tick",context.boundary().completed_tick);u("context","accepted_command_sequence",context.boundary().completed_command_sequence);
      for(Count i=0;i<4;++i)numeric("context","static_range",R::StaticDomainRange,i,0,{7},valid,i);
      for(const char* field:{"original_observed_age","maximum_age","contact_free","completed_history_flags","no_command_in_flight","nominal_anchor"})missing("context",field,"PREVALIDATION_FACT_NOT_RETAINED_BY_CONTEXT_WITNESS");
      u("mesh","cells",mesh.cycles().size());u("mesh","total_cycles",mesh.total());for(Count i=0;i<mesh.cycles().size();++i)u("mesh","cycles",mesh.cycles()[i],i);
      const auto& controls=forecast.nativeCells();u("controls","count",controls.size());for(Count i=0;i<controls.size();++i){integer("controls","cycles",controls[i].cycles,i);numeric("controls","alpha_b",R::RawCellControl,i,0,{8},valid,i);numeric("controls","cycles_i64",R::RawCellControl,i,1,{1},valid,i);}
      integer("capture","requested_mode",static_cast<std::int64_t>(a.requestedMode()));if(a.actualMode())integer("capture","actual_mode",static_cast<std::int64_t>(*a.actualMode()));else missing("capture","actual_mode","NO_COMPLETE_ACTUAL_MODE");
      integer("capture","requested_encoding",static_cast<std::int64_t>(plan.numericEncoding()));missing("capture","whole_actual_encoding","NO_FULL_PUBLISHER_HAS_RUN");integer("capture","initial_kind",static_cast<std::int64_t>(a.initialKind()));
      numeric("capture","chosen_initial",R::ChosenInitial,0,0,{30},a.hasCompleteAssembly());numeric("capture","chosen_initial_kind",R::ChosenInitialKind,0,0,{1},a.hasCompleteAssembly());
      const auto& factors=a.captureShape();u("cost_topology","frozen_terms",factors.terms);u("cost_topology","frozen_rows",factors.rows);u("cost_topology","frozen_largest_term_rows",factors.largest_term_rows);u("cost_topology","frozen_addition_coefficients",factors.addition_coefficients);u("cost_topology","frozen_addition_records",factors.addition_records);
      if(const auto* gate=p->owner->captureOriginalObservation()){u("original_observer","expected_terms",gate->expected_terms);u("original_observer","terms_observed",gate->terms_observed);boolean("original_observer","canonical_observed",gate->canonical_observed);boolean("original_observer","issued",gate->issued);boolean("original_observer","refused",gate->refused);text("original_observer","first_error",gate->first_error);}else missing("original_observer","state","NO_ACTUAL_OBSERVER_STATE");
      boolean("partition","admission_attempted",p->partition->status.attempted);boolean("partition","applied",p->partition->status.applied);boolean("partition","refused",p->partition->status.refused);text("partition","first_error",p->partition->status.first_error);
      text("failure","transport",forecast.transportFailure());text("failure","structural",forecast.structuralRefusal());text("failure","normalization",norm.refusal());text("failure","affine",a.refusal());text("failure","decode_or_cost",decoded.refusal());text("failure","inventory",p->owner->admissionRefusal());
      boolean("status","full_normalized_maps",norm.hasFullNominalMaps());boolean("status","complete_affine",a.hasCompleteAssembly());boolean("status","complete_cost",decoded.hasCompleteCost());
      boolean("capture_status","attached",p->status.attached);boolean("capture_status","closed",p->status.closed);boolean("capture_status","refused",p->status.refused);text("capture_status","first_error",p->status.first_error);
      u("capture_status","attempts",p->status.receipt_attempts);u("capture_status","verified_chunks",p->status.verified_chunks);u("capture_status","ancillary_attempts",p->status.ancillary_receipt_attempts);boolean("capture_status","samples_attempted",p->status.samples_attempted);u("capture_status","samples_completed",p->status.samples_completed);
      boolean("readonly_forensic","refused",p->forensic.refused);u("readonly_forensic","generations",p->forensic.generations);text("readonly_forensic","first_error",p->forensic.first_error);
      if(raw){boolean("raw","value_success",raw->value.success);boolean("raw","has_final_state",raw->value.has_final_state);text("raw","value_error",raw->value.error);boolean("raw","extension_jacobian_success",raw->extension_jacobian_success);integer("raw","first_uncertified_substep",raw->first_uncertified_substep);text("raw","extension_error",raw->error);
        u("raw","substeps",raw->value.substeps.size());u("raw","cycle_states",raw->value.cycle_end_states.size());u("raw","cell_states",raw->value.cell_end_states.size());u("raw","substep_maps",raw->substep_maps.size());u("raw","cycle_maps",raw->cycle_maps.size());u("raw","cell_maps",raw->cell_maps.size());numeric("raw","original_value_indices",R::RawSubstepValueIndicesAggregate,0,0,{raw->value.substeps.size(),3},norm.hasFullNominalMaps());
      }else missing("raw","result","NO_GENUINE_MODEL_RETURN");
      const auto* obs=decoded.captureObservation();if(obs){
#define META_U(name) u("decoder",#name,obs->name)
#define META_B(name) boolean("decoder",#name,obs->name)
        META_U(physical_bytes_read);META_U(consumed_bytes);META_U(metadata_bytes);META_U(expected_scalars);META_U(delivered_scalars);META_U(parsed_terms);META_U(parsed_additions);META_U(active_term);META_U(active_addition);META_U(active_parent);META_U(header_initial_count);META_U(last_scalar_bits);META_U(last_scalar_byte_offset);META_U(pending_u64_bits);META_U(pending_u64_bytes);META_U(pending_u64_start);
        META_B(last_scalar_attempted);META_B(last_scalar_delivered);META_B(last_bits_valid);META_B(refused);META_B(header_complete);META_B(artifact_closed);META_B(hash_valid);
#undef META_U
#undef META_B
        integer("decoder","requested_output",static_cast<std::int64_t>(obs->requested_output));if(obs->actual_input)integer("decoder","actual_input",static_cast<std::int64_t>(*obs->actual_input));else missing("decoder","actual_input","INPUT_ENCODING_NOT_OBSERVED");
        text("decoder","stage",obs->stage);text("decoder","failure",obs->failure);text("decoder","held_physical_prefix_sha256",obs->physical_prefix_sha256);text("decoder","numeric_token_prefix",obs->numeric_token_prefix);
        if(obs->physical_prefix_sha256.empty())missing("decoder","physical_prefix_sha256","NO_HELD_DIGEST_STRING_DO_NOT_RECOMPUTE_HERE");
      }else missing("decoder","observation","DECODER_NOT_OPENED");
      if(obs){const auto& prefix=decoded.parsedMetadataPrefix();u("forensic_cost_prefix","descriptor_count",prefix.size());u("forensic_cost_prefix","actually_parsed_terms",obs->parsed_terms);boolean("forensic_cost_prefix","authoritative",false);for(Count i=0;i<prefix.size();++i){text("forensic_cost_prefix","name",prefix[i].name,i);text("forensic_cost_prefix","units",prefix[i].units,i);u("forensic_cost_prefix","rows",prefix[i].rows,i);u("forensic_cost_prefix","addition_count",prefix[i].additions.size(),i);for(Count j=0;j<prefix[i].additions.size();++j){u("forensic_cost_prefix","sample_index",prefix[i].additions[j].sample_index,i,j);u("forensic_cost_prefix","parent_count",prefix[i].additions[j].parent_rows.size(),i,j);} }
      }
      const CostInputRecipe* sealed=nullptr;try{sealed=&decoded.costOutcome().originalInputRecipe();}catch(const std::exception&){}
      if(sealed){file("sealed_cost_input",sealed->file);u("cost_topology","terms",sealed->terms.size());for(Count i=0;i<sealed->terms.size();++i){const auto& term=sealed->terms[i];text("cost_term","name",term.name,i);text("cost_term","units",term.units,i);u("cost_term","rows",term.rows,i);u("cost_term","order",i,i);u("cost_term","addition_count",term.additions.size(),i);
          for(Count j=0;j<term.additions.size();++j){const auto& addition=term.additions[j];u("cost_addition","sample_index",addition.sample_index,i,j);u("cost_addition","order",j,i,j);u("cost_addition","parent_count",addition.parent_rows.size(),i,j);
            // Ordered parents are full U64 numeric references, not a lossy summary.
            numeric("cost_addition","parent_rows",R::CostAdditionRows,i,j,{addition.parent_rows.size()},valid,i,j);numeric("cost_addition","coefficients",R::CostAdditionCoefficients,i,j,{addition.parent_rows.size(),30},valid,i,j);}
        }}else missing("cost_topology","sealed_terms","NO_AUTHORITATIVE_SEALED_DESCRIPTOR");
      Count regionOrdinal=0;auto trace=[&](Count layer,const RetainedNumericRegionView& region){const Count ordinal=regionOrdinal++;u("math_region","layer",layer,ordinal);const auto& t=region.trace();text("math_region","role",region.role(),ordinal);u("math_region","defined_count",region.definedCount(),ordinal);text("math_region","stage",t.stage,ordinal);text("math_region","memory_stage",t.memory_stage,ordinal);u("math_region","item",t.item,ordinal);u("math_region","row",t.row,ordinal);u("math_region","column",t.column,ordinal);u("math_region","addition",t.addition,ordinal);u("math_region","memory_item",t.memory_item,ordinal);boolean("math_region","current_complete",t.complete,ordinal);boolean("math_region","construction_completed",t.construction_completed,ordinal);for(Count j=0;j<32;++j)u("math_region","written",t.written[j],ordinal,j);};
      if(norm.hasRetainedRegions())norm.withRetainedRegions([&](const RetainedNumericRegionView& r){trace(0,r);});else missing("math_region","normalizer","NO_RETAINED_NORMALIZER_STORAGE");
      if(a.hasRetainedRegions())a.withRetainedRegions([&](const RetainedNumericRegionView& r){trace(1,r);});else missing("math_region","affine","NO_RETAINED_AFFINE_STORAGE");
      if(decoded.cost_&&decoded.cost_->hasRetainedRegions())decoded.cost_->withRetainedRegions([&](const RetainedNumericRegionView& r){trace(2,r);});else missing("math_region","cost","NO_RETAINED_COST_STORAGE");
      auto io=[&](const char* family,Count i,const ChunkIOObservation& o){text(family,"stage",o.stage,i);u(family,"attempted_index",o.attempted_index,i);u(family,"encoded_or_decoded",o.encoded_or_decoded,i);u(family,"physical_bytes",o.physical_bytes,i);u(family,"consumed_bytes",o.consumed_bytes,i);u(family,"pending_bytes",o.pending_bytes,i);boolean(family,"last_bits_valid",o.last_bits_valid,i);if(o.last_bits_valid)u(family,"last_scalar_bits",o.last_scalar_bits,i);boolean(family,"hash_valid",o.hash_valid,i);boolean(family,"refused",o.refused,i);text(family,"first_error",o.first_error,i);text(family,"physical_prefix_sha256",o.physical_prefix_sha256,i);};
      for(Count i=0;i<p->attempts.size();++i){const auto& attempt=p->attempts[i];const auto& w=attempt.write_;const auto& r=w.record;
        u("attempt","role",static_cast<Count>(attempt.role_),i);u("attempt","primary",attempt.primary_,i);u("attempt","secondary",attempt.secondary_,i);u("attempt","generation",attempt.generation_,i);u("attempt","original_sequence",attempt.attempt_sequence_,i);integer("attempt","computed_state",static_cast<std::int64_t>(attempt.computed_state_),i);
        text("attempt","storage_traversal",attempt.storage_traversal_,i);text("attempt","assignment_traversal",attempt.assignment_traversal_,i);boolean("attempt","source_matches",attempt.source_origin_==p->source_origin,i);boolean("attempt","cost_matches",attempt.cost_origin_==p->actual_cost_origin,i);boolean("attempt","partition_matches",attempt.partition_==p->partition,i);
        boolean("attempt","original_scope",attempt.original_scope_,i);boolean("attempt","canonical_scope",attempt.canonical_scope_,i);boolean("attempt","sample_scope",attempt.sample_scope_,i);u("attempt","cell",attempt.sample_cell_,i);u("attempt","tick",attempt.sample_tick_,i);u("attempt","cycle",attempt.sample_cycle_,i);u("attempt","half",attempt.sample_half_,i);
        u("attempt","rank",r.spec.dimensions.size(),i);for(Count j=0;j<r.spec.dimensions.size();++j)u("attempt","dimension",r.spec.dimensions[j],i,j);integer("attempt","kind",static_cast<std::int64_t>(r.spec.kind),i);integer("attempt","classification",static_cast<std::int64_t>(r.spec.classification),i);integer("attempt","encoding",static_cast<std::int64_t>(r.encoding),i);
        text("attempt","root",r.root_path,i);text("attempt","name",r.spec.relative_name,i);text("attempt","role_label",r.spec.role,i);text("attempt","sha256",r.sha256,i);u("attempt","count",r.count,i);u("attempt","bytes",r.bytes,i);u("attempt","device",r.device,i);u("attempt","inode",r.inode,i);u("attempt","directory_device",r.directory_device,i);u("attempt","directory_inode",r.directory_inode,i);boolean("attempt","closed_fsynced",r.closed_fsynced,i);
        text("attempt_write","stage",w.observation.stage,i);text("attempt_write","first_error",w.observation.first_error,i);boolean("attempt_write","refused",w.observation.refused,i);u("attempt_write","physical_bytes",w.observation.physical_bytes,i);u("attempt_write","encoded",w.observation.encoded_or_decoded,i);text("attempt_write","prefix_sha256",w.observation.physical_prefix_sha256,i);
        boolean("attempt","comparison_attempted",attempt.comparison_attempted_,i);boolean("attempt","expected_valid",attempt.expected_valid_,i);boolean("attempt","mismatch",attempt.mismatch_,i);u("attempt","comparison_index",attempt.mismatch_index_,i);integer("attempt","expected_kind",static_cast<std::int64_t>(attempt.expected_.kind),i);integer("attempt","actual_kind",static_cast<std::int64_t>(attempt.actual_.kind),i);
        if(attempt.expected_valid_){MetadataFact bits;bits.family="attempt";bits.field="expected_bits";bits.index=i;bits.kind=(attempt.expected_.kind==ChunkScalarKind::F64||attempt.expected_.kind==ChunkScalarKind::FailureF64Bits)?MetadataKind::Ieee64Bits:MetadataKind::U64;bits.unsigned_value=attempt.expected_.bits;emit(bits);}else missing("attempt","expected_bits","EXPECTED_SCALAR_NOT_OBSERVED_VALID",i);
        if(attempt.comparison_attempted_){MetadataFact bits;bits.family="attempt";bits.field="actual_bits";bits.index=i;bits.kind=(attempt.actual_.kind==ChunkScalarKind::F64||attempt.actual_.kind==ChunkScalarKind::FailureF64Bits)?MetadataKind::Ieee64Bits:MetadataKind::U64;bits.unsigned_value=attempt.actual_.bits;emit(bits);}else missing("attempt","actual_bits","ACTUAL_SCALAR_NOT_OBSERVED",i);
        io("attempt_write_frontier",i,w.observation);
        if(attempt.readback_){const auto& read=*attempt.readback_;io("attempt_read_frontier",i,read.observation);boolean("attempt_read","exact_readback",read.exact_readback,i);text("attempt_read","sha256",read.observed_sha256,i);text("attempt_read","stage",read.observation.stage,i);text("attempt_read","first_error",read.observation.first_error,i);boolean("attempt_read","refused",read.observation.refused,i);u("attempt_read","consumed_bytes",read.observation.consumed_bytes,i);}else missing("attempt_read","outcome","NO_INDEPENDENT_READBACK_OUTCOME",i);
      }
      u("quota","current_live_slots",p->budget.liveSlots());u("quota","current_cumulative_charges",p->budget.cumulativeCharges());u("quota","live_ceiling",p->budget.liveCeiling());u("quota","charge_ceiling",p->budget.chargeCeiling());u("quota","actual_metadata_bytes_so_far",p->budget.metadataBytes());u("quota","actual_unique_output_bytes_so_far",p->budget.outputBytes());u("quota","output_ceiling",p->budget.outputCeiling());u("quota","metadata_ceiling",ResourcePolicyV2::metadata_bytes);
      missing("execution","early_failure_owner_variants","PRE_MODEL_OR_PRE_AFFINE_OWNER_NOT_SUPPORTED_BY_THIS_SESSION");
      boolean("scope","full_capture_complete",false);boolean("scope","full_flow_accepted",false);static constexpr const char* claims[]={"segment","two_sided_ball","admissibility","execution","safety","uniform_accuracy","controller_readiness"};for(Count i=0;i<7;++i)boolean("scope",claims[i],false);text("scope","phase5","NOT_ACCEPTED");text("scope","phase6","NOT_STARTED");
    }catch(const std::exception& e){evidencePoison(*p,e.what());throw;}catch(...){evidencePoison(*p,"NONSTANDARD_METADATA_BORROW_FAILURE");throw;}
  }
  static void references(std::shared_ptr<CaptureLeafState> p,const ReferenceConsumer& caller){
    try{orderedAttempts(p);EvidenceGuard guard(*p,40);const auto sink=caller;p->evidenceHealthy();need(static_cast<bool>(sink),"empty frozen reference visitor");
      auto emit=[&](ReferenceFact f){p->evidenceHealthy();p->budget.chargeScratchOrCopy(40);if(!f.zero_block&&!f.empty_concatenation)bindReference(*p,f);ReferenceBinding b{p,f,++p->evidence_generation};const ReferenceLeafView view(&b);sink(view);p->evidenceHealthy();};
      const auto& decoded=p->owner->genuineSource();const auto& a=decoded.originalAssembly();need(a.captureOriginToken()==p->source_origin,"reference source changed");const auto& norm=a.originalNormalization();
      // No invented mapping on incomplete normalization. Failure facts remain metadata.
      need(norm.hasFullNominalMaps()&&a.hasCompleteAssembly(),"complete actual reference topology unavailable; required obligation missing");
      const auto& forecast=norm.originalForecast();const auto* raw=forecast.originalResult();need(raw,"reference raw owner missing");const auto& mesh=forecast.mesh();const Count n=mesh.cycles().size(),du=a.capturePlan().du(),dy=a.capturePlan().dy();
      const bool valid=decoded.hasCompleteCost()&&!p->status.closed&&!p->status.refused;
      auto mapRefs=[&](ReferenceUse use,Count i,Count group,const phase5_public_coupled_augmented_extension::Map& m,Count tick){
        need(m.cell>=0&&m.cycle>=0&&m.half>=0,"negative normalized native roster");
        Count part=0;auto send=[&](R role,std::initializer_list<Count> shape){auto f=reference(use,i,part++,role,group,i,shape,valid);f.cell=m.cell;f.cycle=m.cycle;f.half=m.half;f.tick=tick;emit(f);};
        send(R::RawMapCellA,{size(m.cell_A.rows()),size(m.cell_A.cols())});send(R::RawMapCellB,{size(m.cell_B.rows()),size(m.cell_B.cols())});send(R::RawMapCellDefect,{size(m.cell_defect.size())});
        send(R::RawMapCellOrigin,{packedCount(m.cell_origin)});send(R::RawMapEndpoint,{packedCount(m.state)});send(R::RawMapInput,{size(m.input.size())});send(R::RawMapIndices,{3});
      };
      Count tick=0;for(Count i=0;i<n;++i){tick=add(tick,mul(2,mesh.cycles().at(i)));mapRefs(ReferenceUse::NormalizedCell,i,2,raw->cell_maps.at(i),tick);}
      for(Count i=0;i<raw->substep_maps.size();++i){mapRefs(ReferenceUse::NormalizedSample,i,0,raw->substep_maps.at(i),add(i,1));mapRefs(ReferenceUse::SampleRecipe,i,0,raw->substep_maps.at(i),add(i,1));
        const auto& m=raw->substep_maps.at(i);const Count cell=m.cell;Count part=7;
        for(R role:{R::BoundaryOffset,R::BoundaryControl,R::BoundaryInitial}){auto f=role==R::BoundaryOffset?reference(ReferenceUse::SampleRecipe,i,part,role,cell,0,{30},valid):role==R::BoundaryControl?reference(ReferenceUse::SampleRecipe,i,part,role,cell,0,{30,du},valid):reference(ReferenceUse::SampleRecipe,i,part,role,cell,0,{30,30},valid);++part;f.cell=cell;f.cycle=m.cycle;f.half=m.half;f.tick=add(i,1);emit(f);}
        auto control=reference(ReferenceUse::SampleRecipe,i,10,R::RawCellControl,cell,0,{8},valid);control.cell=cell;control.cycle=m.cycle;control.half=m.half;control.tick=add(i,1);control.destination_offset=mul(8,cell);emit(control);
        auto chosen=reference(ReferenceUse::SampleRecipe,i,11,R::ChosenInitial,0,0,{30},valid);chosen.cell=cell;chosen.cycle=m.cycle;chosen.half=m.half;chosen.tick=add(i,1);emit(chosen);
      }
      for(Count i=0;i<raw->cycle_maps.size();++i)mapRefs(ReferenceUse::NormalizedCycle,i,1,raw->cycle_maps.at(i),mul(2,add(i,1)));
      // All P blocks including initial identity; appended U rows are exact zero.
      for(Count i=0;i<=n;++i){auto f=reference(ReferenceUse::InitialSelector,0,i,R::BoundaryInitial,i,0,{30,30},valid);f.destination_offset=mul(mul(30,i),30);emit(f);}
      ReferenceFact zero;zero.use=ReferenceUse::InitialSelector;zero.part=add(n,1);zero.zero_block=true;zero.rank=2;zero.dimensions={du,30,0,0};zero.count=mul(du,30);zero.destination_offset=mul(a.capturePlan().dx(),30);zero.source_valid=valid;emit(zero);
      const auto& sealed=decoded.costOutcome().originalInputRecipe();Count row=0;
      if(sealed.terms.empty())for(Count part=0;part<4;++part){auto f=part==0||part==2?reference(ReferenceUse::CanonicalConcatenation,0,part,R::CanonicalOrderedConcatenation,0,part,{0,part==0?dy:du},valid):reference(ReferenceUse::CanonicalConcatenation,0,part,R::CanonicalOrderedConcatenation,0,part,{0},valid);f.empty_concatenation=true;emit(f);}
      for(Count i=0;i<sealed.terms.size();++i){const Count rows=sealed.terms[i].rows;
        for(Count part=0;part<4;++part){const R role=part==0?R::OriginalUsedFactor:part==1?R::OriginalUsedOffset:part==2?R::TermCondensedFactor:R::TermCondensedOffset;const Count columns=part==0?dy:part==2?du:1;
          auto f=part==0||part==2?reference(ReferenceUse::CanonicalConcatenation,i,part,role,i,0,{rows,columns},valid):reference(ReferenceUse::CanonicalConcatenation,i,part,role,i,0,{rows},valid);
          f.destination_offset=mul(row,columns);f.requires_original_scope=part<2;emit(f);
        }row=add(row,rows);
      }need(row==a.captureShape().rows&&sealed.terms.size()==a.captureShape().terms,"canonical concatenation has missing/extra rows or terms");
      // Actual summed H/g/ell/c0/c are not recomputed or represented by concat.
    }catch(const std::exception& e){evidencePoison(*p,e.what());throw;}catch(...){evidencePoison(*p,"NONSTANDARD_REFERENCE_BORROW_FAILURE");throw;}
  }
  static void coverage(std::shared_ptr<CaptureLeafState> p,const CoverageConsumer& caller){
    try{orderedAttempts(p);EvidenceGuard guard(*p,20);const auto sink=caller;p->evidenceHealthy();need(static_cast<bool>(sink),"empty frozen coverage visitor");
      auto check=[&](RequiredField f){p->budget.chargeScratchOrCopy(20);CoverageObligation o;o.required=f;
        if(!f.shape_known){o.state=CoverageState::UnknownShape;o.reason="MISSING_AUTHORITATIVE_ACTUAL_SHAPE";}
        else if(f.availability==FieldAvailability::AbsentUpstream){o.state=CoverageState::AbsentUpstream;o.reason="GENUINE_UPSTREAM_FIELD_ABSENT";}
        else if(f.scalar_kind==RequiredScalarKind::Metadata||f.scalar_kind==RequiredScalarKind::SourceReference||f.scalar_kind==RequiredScalarKind::Composite){o.state=CoverageState::UnsupportedCompound;o.reason="METADATA_OR_REFERENCE_RECONSTRUCTION_OR_FAILURE_PUBLICATION_NOT_VERIFIED";}
        else{
          Count count=1;for(Count k=0;k<f.rank;++k)count=mul(count,f.dimensions[k]);
          const auto& d=p->owner->genuineSource();const auto& a=d.originalAssembly();
          if(const auto* actual=lookup(*p,{f.role,f.primary,f.secondary})){const auto& attempt=*actual;++o.matching_attempts;
            need(o.matching_attempts==1,"duplicate private obligation receipt");const auto& record=attempt.write_.record;
            need(attempt.source_origin_==p->source_origin&&attempt.cost_origin_==p->actual_cost_origin&&attempt.partition_==p->partition&&attempt.generation_>0,"coverage foreign actual source/cost/partition/generation");
            need(record.count==count&&record.spec.dimensions.size()==f.rank,"coverage exact shape/count mismatch");for(Count k=0;k<f.rank;++k)need(record.spec.dimensions[k]==f.dimensions[k],"coverage exact dimension mismatch");
            const auto kind=f.scalar_kind==RequiredScalarKind::U64?ChunkScalarKind::U64:f.scalar_kind==RequiredScalarKind::I64?ChunkScalarKind::I64:ChunkScalarKind::F64;need(record.spec.kind==kind,"coverage actual scalar type mismatch");
            need(std::string_view(attempt.storage_traversal_)==storageTraversal(f.role),"exact actual storage/packing traversal mismatch");if(f.role==R::DenseSolution)need(std::string_view(attempt.assignment_traversal_)=="column-then-reverse-row","Dense solution assignment traversal mismatch");
            const bool original=(f.role>=R::OriginalUsedFactor&&f.role<=R::OriginalUsedConstant)||(f.role>=R::OriginalDirectValue&&f.role<=R::OriginalCondensedHessian);
            if(original){need(attempt.original_scope_,"required ORIGINAL actual callback scope absent");const bool canonical=f.primary==a.captureShape().terms;need(attempt.canonical_scope_==canonical,"original term versus canonical scope mismatch");}
            const bool sample=f.role>=R::SampleEvaluatedOffset&&f.role<=R::SampleEvaluatedInitial;
            if(sample){need(attempt.sample_scope_&&a.originalNormalization().hasFullNominalMaps(),"required actual sample scope/source absent");const auto& native=a.originalNormalization().maps().samples().at(f.primary);need(attempt.sample_cell_==native.cell()&&attempt.sample_tick_==native.physicalTick()&&attempt.sample_cycle_==native.cycle()&&attempt.sample_half_==native.half(),"coverage exact sample provenance mismatch");}
            o.required.actual_leaf_bound=true;o.required.defined_computed=attempt.computed_state_;
            o.required.bytes_captured=attempt.write_.closedChunk();o.required.exact_readback=attempt.readback_&&attempt.readback_->exact_readback&&!attempt.readback_->observation.refused&&!attempt.mismatch_;
            o.state=CoverageState::Unverified;o.reason="PRIVATE_ATTEMPT_NOT_CURRENT_COMPLETE_EXACT_READBACK";
            if(!p->status.closed&&!p->status.refused&&d.hasCompleteCost()&&p->partition->status.applied&&!p->partition->status.refused&&p->budget.sameCase(p->partition->budget)&&attempt.computed_state_==DefinedComputedState::ComputedOriginal&&record.encoding==p->budget.numericEncoding()&&attempt.write_.closedChunk()&&attempt.readback_&&attempt.readback_->exact_readback&&!attempt.readback_->observation.refused&&!attempt.mismatch_){o.state=CoverageState::VerifiedPrivateNumeric;o.reason="EXACT_PRIVATE_NUMERIC_ONLY_METADATA_REFERENCE_GLOBAL_CLOSURE_PENDING";}
          }
        }
        ObligationBinding b{p,o,++p->evidence_generation};const CoverageObligationView view(&b);sink(view);p->evidenceHealthy();
      };
      // Base catalogue composite control is deliberately split to actual f64/i64.
      p->owner->withRequirements([&](const RequiredField& required){if(required.role==R::RawCellControl){auto f=required;f.scalar_kind=RequiredScalarKind::F64;f.rank=1;f.dimensions={8,0,0,0};check(f);f.secondary=1;f.scalar_kind=RequiredScalarKind::I64;f.dimensions={1,0,0,0};check(f);}else check(required);});
      const auto& a=p->owner->genuineSource().originalAssembly();const auto& forecast=a.originalNormalization().originalForecast();const auto& m=forecast.verifiedMetadata();
      auto extra=[&](R role,Count i,std::initializer_list<Count> dims,RequiredScalarKind kind){RequiredField f;f.role=role;f.primary=i;f.rank=dims.size();Count k=0;for(Count d:dims)f.dimensions[k++]=d;f.scalar_kind=kind;f.availability=FieldAvailability::OwnedSourceReference;check(f);};
      Count k=0;for(const auto* v:{&m.masses,&m.armature,&m.gravity,&m.R,&m.B,&m.damping}){extra(R::CachedMetadataVector,k,{size(v->size())},RequiredScalarKind::F64);++k;}
      k=0;for(const auto* v:{&m.idx_q,&m.idx_v,&m.joint_nq,&m.joint_nv}){extra(R::CachedMetadataIndices,k,{v->size()},RequiredScalarKind::I64);++k;}
      extra(R::CachedMetadataDimensions,0,{2},RequiredScalarKind::I64);extra(R::ActualContextInitial,0,{30},RequiredScalarKind::F64);extra(R::PreviousControlHistory,0,{8},RequiredScalarKind::F64);extra(R::ActualBoundaryCounters,0,{2},RequiredScalarKind::U64);for(Count i=0;i<4;++i)extra(R::StaticDomainRange,i,{7},RequiredScalarKind::F64);
      const auto* raw=forecast.originalResult();if(raw)extra(R::RawSubstepValueIndicesAggregate,0,{raw->value.substeps.size(),3},RequiredScalarKind::I64);
      // All unsupported/absent facts remain missing. No aggregate success token.
    }catch(const std::exception& e){evidencePoison(*p,e.what());throw;}catch(...){evidencePoison(*p,"NONSTANDARD_COVERAGE_OBLIGATION_FAILURE");throw;}
  }
