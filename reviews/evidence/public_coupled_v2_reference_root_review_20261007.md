# Independent root review: public coupled v2 reference contract

Verdict: **PASS_FIXED_FR3_REFERENCE_CONTRACT_V2_INDEPENDENT**. This verifies a small reference-coefficient and unsupported-input correction. Existing public model/static parameters, friction solver and physical step are unchanged. No whole-environment freeze, generalized model accuracy, new holdout, domain enlargement or Phase5 acceptance is established.

The [independent script](../../scripts/phase5/audit_public_coupled_reference_v2.py) checked all **88 producer-prelisted source/input hashes before and after** a fresh isolated run. Original v1's 40 frozen entries remain present with identical hashes. Execution uses copied frozen source/static bytes, also checked against those identities. Public v2 model source SHA is `89a0ce2122aaa709afe3195d1cca269debca3e70710462cbdbeea37bd48e480a`. These checks cover the named source/model/mesh/native dependency inputs, not every file in Python or the host. Full archive member/closure verification is coordinated separately by root.

The source correctly changes standard positive-solref friction reference damping to

\[
B=2/(d_{max}\,timeconst),
\]

removing the erroneous dampratio multiplier. Friction reference stiffness is zero; the standard damping formula does not depend on dampratio. Current frozen `solref=(.02,1)` therefore yields exactly the previous B and exactly the same training predictions. The implementation rejects nonfinite/nonpositive solref, accepts only the previously inspected seven copies of `solimp=(.9,.95,.001,.5,2)`, and explicitly rejects timeconst below `2*.002=.004` s. MuJoCo's reference-safety substitution is not implemented; rejecting that unsupported regime is declared rather than silently approximating it. This remains a fixed seven-coordinate FR3 prototype.

Fresh results use the existing root fixtures and original fixed training windows, with no new scan or test-design expansion:

- All seven root friction-box fixtures match the independent oracle, with maximum force difference `2.220446049250313e-16` N·m and original KKT residual below `1e-10`.
- Synthetic dampratios `.5` and `2` both give standard B `105.26315789473685` s⁻¹ on all axes, exactly equal to the ratio-one baseline. These alter copied metadata only; no plant/model accuracy trial occurred.
- All five existing negative cases reject: timeconst `.003`, zero dampratio, negative timeconst, nonfinite dampratio and changed solimp profile.
- Nineteen fixed TRAIN91011 windows at ticks `100,500,1250,2400,2500` and `2/4/40/800` ms retain warmup and stopping coverage. V1/v2 endpoint q/v differences are strictly zero. Selected actual endpoint errors are at most `4.440892098500626e-16` rad and `2.288967626551397e-15` rad/s.
- Tick2500's incomplete 800 ms request remains unscorable with only 380 available substeps; it is neither shortened nor treated as a passed window. The tick2400 800 ms case retains its 200 stopping substeps.

Each forecast initializes q/v only at its start and uses its own public-model states plus recorded accepted targets thereafter. Only old TRAIN91011 raw SHA `ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce` was read. There was no full-TRAIN rescan, evaluation/91012/v3 use, fitting, plant state/commands or authoritative edit. Parameter-contract correctness does not validate predictions for changed parameters, contacts, unknown forces or different robots.

[Detailed JSON](public_coupled_v2_reference_root_review_20261007.json) records all 88 identities and fresh fixture/window/rejection results. Unique immutable output `results/phase5-reference/root-public-coupled-reference-v2-independent-20261007-v1` contains source and execution-packet snapshots plus READY. Dell workspace is `/home/codextransfer/clean-audits/public-coupled-reference-v2-independent-20261007-v1`. Final independent source SHA is `b512b50f2f70264c02261ac3e4e7f60944c15ade2e484dcf76b8233ab101d5ae`.
