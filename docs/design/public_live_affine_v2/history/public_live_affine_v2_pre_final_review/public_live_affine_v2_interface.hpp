#pragma once
// SOURCE INTERFACE PROPOSAL ONLY. New namespace; no old ABI/limits modified.
#include "public_coupled_augmented_extension.hpp"
#include <cstdint>
#include <string>
#include <vector>
namespace phase5_public_live_affine_v2 {
using State=phase5_public_coupled_augmented::State;
using Cell=phase5_public_coupled_augmented::Cell;
using RawResult=phase5_public_coupled_augmented_extension::Result;
enum class MeshPolicy {UniformExact,BalancedInteger,ExplicitCycles};
enum class InitialKind {LiveActual,AlgebraTest};
enum class CaptureMode {CompactComplete,DenseAuditComplete};
struct BoundaryId {std::uint64_t completed_tick=0,completed_command_sequence=0;};
struct ObservedActual {
 Eigen::VectorXd q,v;BoundaryId boundary;
 std::string immutable_observation_id;double state_age=0;
 bool current_contact_free=false; // trusted current observer fact, not future safety
};
struct AcceptedCommandHistory {Eigen::VectorXd C,w,previous_alpha;BoundaryId boundary;};
struct ProgressHistory {double s=0,r=0,previous_b=0;BoundaryId boundary;};
struct NominalAnchor {State point;BoundaryId boundary;};
struct HorizonSpec {
 std::uint32_t steps=20,total_macro_cycles=200;
 MeshPolicy policy=MeshPolicy::UniformExact;
 std::vector<std::uint32_t> explicit_cycles;
};
struct CycleMesh {std::vector<std::uint32_t> cycles;std::uint32_t total=0;};
struct Invocation {
 ObservedActual actual_physical;AcceptedCommandHistory actual_command;
 ProgressHistory actual_progress;NominalAnchor nominal;
 CycleMesh mesh;std::vector<Cell> nominal_cells;std::string invocation_digest;
};
struct VerifiedModelProfile; // private factory: producerELF/source/XML/constants/
                            // metadata/SDK/policy binding, never a forged f1 ID
class PinnedModelHandle;
struct ReviewedForecastPermission;
class OwnedPublicForecast; // move-only genuine raw result+Invocation+profile
class NormalizedNominalMaps; // nominal support only; ALL seven claims false
struct ResourcePolicyV2;
struct CostTerm {
 std::string name,units;Eigen::MatrixXd F;Eigen::VectorXd f0,linear;double c0=0;
 struct Addition {std::size_t sample_index;std::vector<std::size_t> rows;Eigen::MatrixXd coefficient;};
 std::vector<Addition> sample_additions; // C: rows.size()*30, explicit row embedding
};
struct CommandProposal {Eigen::VectorXd C_next,w_next,alpha;double s_next,r_next,b;BoundaryId from;};
CycleMesh planMesh(const HorizonSpec&,const ResourcePolicyV2&);
OwnedPublicForecast forecastPublic(PinnedModelHandle&,const Invocation&,const ReviewedForecastPermission&);
NormalizedNominalMaps normalizePublic(OwnedPublicForecast&&,const ResourcePolicyV2&);
// Failure/result ownership contract must preserve RawResult and no full maps.
// LiveActual builds x0 from actual fields, validates original closed live domain;
// AlgebraTest accepts explicit finite x0 (including negative r) with no proposal.
struct AssemblyInitial {InitialKind kind;State explicit_algebra_initial;};
struct AssemblyAndCost;
AssemblyAndCost assembleAffine(const NormalizedNominalMaps&,const Invocation&,
 const AssemblyInitial&,const std::vector<CostTerm>&,const ResourcePolicyV2&,CaptureMode);
// Pure request arithmetic from ACTUAL accepted history and candidateu0.
// No accepting/issuing command, no nominalendpoint alias or physicalqdd claim.
CommandProposal first4msRequest(const AcceptedCommandHistory&,const ProgressHistory&,
 const Eigen::VectorXd& candidate_alpha,double candidate_b);
} // namespace phase5_public_live_affine_v2
