#pragma once
#include <Eigen/Core>
#include <cstddef>
#include <string>
#include <vector>

namespace phase5_public_coupled_augmented_extension { struct Result; }

namespace phase5_public_affine_horizon {
using Matrix = Eigen::MatrixXd;
using Vector = Eigen::VectorXd;

// SOURCE INTERFACE DRAFT ONLY. No solver, controller or nonlinear model call.
// Fixed v1 development-diagnostic limits, not a project horizon guarantee.
// Core and CLI reject altered limit/tolerance values in this version.
// Fields are exposed for exact metadata serialization, not upward configuration.
struct Limits {
  std::size_t max_cases=32, max_cells=16, max_samples=512;
  std::size_t max_nx=64, max_nu=16, max_terms=32, max_factor_rows=256;
  std::size_t max_matrix_elements=2000000, max_document_bytes=67108864;
  std::size_t max_problem_numeric_elements=8000000;
  std::size_t max_cli_numeric_elements=16000000;
  double arithmetic_abs=2e-13, arithmetic_rel=2e-13;
};
// Shared across all cases, including cases that later fail. No budget reset
// after refusal; checked integer arithmetic must precede every allocation.
struct CliBudget { std::size_t charged_numeric_elements=0; };
struct ProblemBudget {
  CliBudget& cli;
  std::size_t charged_numeric_elements=0;
  const Limits& limits;
  void reserve(std::size_t numeric_elements);
};
struct Scope {
  bool connecting_segment=false, ball=false, admissibility=false;
  bool execution=false, safety=false, uniform_error_bound=false;
  bool controller_readiness=false;
};
struct SourceIdentity {
  std::string kind, artifact_id, file_sha256, row_name, source_binary_sha256;
  std::string certificate_name;
  bool full_nominal_source_certified=false;
  // A changed actual initial state is algebra only, irrespective of this flag.
};
struct Transition { Matrix A,B; Vector defect; int cycles=1; };
struct Sample {
  std::size_t cell=0; int cycle=1, half=1;
  Matrix A,B; Vector defect;
  // These A/B/defect are cumulative from this cell's origin, never cycle-local.
};
struct NominalCell { Vector origin,input,endpoint; };
struct NominalSample { Vector origin,input,endpoint; };
struct Problem {
  std::size_t nx=0, nu=0;
  Vector actual_initial;
  std::vector<Transition> cells;
  std::vector<Sample> samples;
  SourceIdentity source;
  // Empty for generic synthetic algebra; literal archived values for public.
  std::vector<NominalCell> nominal_cells;
  std::vector<NominalSample> nominal_samples;
};
struct AffineView { Vector offset; Matrix control,initial; };
struct SampleView {
  std::size_t cell=0; int cycle=1,half=1;
  AffineView recursive;
  // sample = lifted_factor * y + lifted_offset, y=[z0..zN;U].
  Matrix lifted_factor; Vector lifted_offset;
  AffineView eliminated;
};
struct Assembly {
  std::vector<AffineView> recursive_states;
  Matrix L,E; Vector f;
  Matrix initial_selector;
  Matrix X_control,X_initial; Vector X_offset;
  Matrix T; Vector t; // y=T*U+t; append identity control block.
  std::vector<SampleView> samples;
  Vector nominal_cell_defect_residual_max, nominal_sample_defect_residual_max;
  // Residuals are reported even when within the declared arithmetic tolerance.
};
struct SampleFactor {
  std::size_t sample_index=0;
  Matrix coefficient; // same row count as parent F; columns nx.
};
struct FactorTerm {
  std::string name,units;
  Matrix F; Vector f0,linear; double constant=0;
  std::vector<SampleFactor> sample_additions;
  // J=.5||F*y+f0||^2+linear^T*y+constant. No implicit weights/default terms.
};
struct CondensedTerm {
  std::string name,units;
  Matrix used_F; Vector used_f0,used_linear; double used_constant=0;
  Matrix factor,H; Vector offset,g; double constant=0;
};
struct Objective {
  std::vector<CondensedTerm> terms;
  CondensedTerm sum;
  // used_F/used_f0 and factor/offset concatenate in input term order.
  // used_linear/used_constant and H/g/constant accumulate in input term order.
  // Zero terms: used_F 0*dy, used_f0 empty, used_linear zero(dy),
  // used_constant 0; factor 0*du, offset empty, H/g/constant zero.
};
struct Evaluation {
  double lifted_value=0,condensed_value=0;
  Vector lifted_chain_gradient,condensed_gradient;
  Matrix lifted_chain_hessian,condensed_hessian;
  // Stored raw H remains unchanged. Literal condensed polynomial derivatives
  // use symmetric_H=.5*(H+H.transpose()), not raw H when roundoff differs.
};
// Every operation checks dimensions/resources before allocation, finite input
// and each intermediate product/sum; failure throws, yielding no assembly.
Assembly assemble(const Problem&,const Limits&,ProblemBudget&);
Objective substitute(const Assembly&,const std::vector<FactorTerm>&,const Limits&,ProblemBudget&);
Evaluation evaluate(const Assembly&,const CondensedTerm&,const Vector& U,const Limits&,ProblemBudget&);

// normalize_public_native consumes existing values only, never constructs Model.
// Uses Map.cell_A/cell_B/cell_defect/cell_origin even for Result.cell_maps.
// Native caller must supply verified source identity and exact nominal descriptor.
Problem normalize_public_native(
    const phase5_public_coupled_augmented_extension::Result& saved,
    const Problem& nominal_descriptor,const SourceIdentity&,const Limits&,ProblemBudget&);
// JSON normalization/byte verification belongs to the separate CLI loader:
// archived original_input+original_output -> Problem, before assemble().
} // namespace phase5_public_affine_horizon
