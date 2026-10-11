#pragma once
#include "session_primitives.hpp"
#include "public_coupled_augmented_extension.hpp"
#include <memory>
#include <vector>
namespace phase5_active_session_v1 {
using RawResult=phase5_public_coupled_augmented_extension::Result;
using NativeMetadata=phase5_public_coupled_v2::ModelMetadata;
struct NominalControl { JointVector alpha{}; double b=0; };
struct SessionPins {
 FileIdentity producer,xml,constants,expected_metadata;
 std::vector<FileIdentity> dependencies,loaded_libraries;
 std::string session_id;
};
namespace detail {struct SessionStorage;struct ForecastStorage;struct NormalizationFactory;}
class OwnedPublicForecast final {
 public:
 OwnedPublicForecast(const OwnedPublicForecast&)=delete;
 OwnedPublicForecast& operator=(const OwnedPublicForecast&)=delete;
 OwnedPublicForecast(OwnedPublicForecast&&) noexcept;
 OwnedPublicForecast& operator=(OwnedPublicForecast&&) noexcept;
 ~OwnedPublicForecast();
 const RawResult* originalResult() const;
 const std::string& transportFailure() const;
 const std::string& structuralRefusal() const;
 const LiveActualContext& actualContext() const;
 const CycleMesh& mesh() const;
 const std::vector<phase5_public_coupled_augmented::Cell>& nativeCells() const;
 const std::string& invocationSha256() const;
 double originalObservedAge() const;
 const NativeMetadata& verifiedMetadata() const;
 const SessionPins& startupPins() const;
 bool bindingVerified() const noexcept;
 private:
 explicit OwnedPublicForecast(std::unique_ptr<detail::ForecastStorage>);
 CaseBudget& normalizationBudget();
 const ResourcePlan& normalizationPlan() const;
 const char* normalizationCertificate() const;
 std::unique_ptr<detail::ForecastStorage> storage_;
 friend class Session;
 friend struct detail::NormalizationFactory;
};
// Prediction session only. Runtime commit/observer ownership is a separate seam;
// this factory accepts completed-boundary inputs and cannot step any plant.
class Session final {
 public:
 explicit Session(const SessionPins&);
 Session(const Session&)=delete;Session& operator=(const Session&)=delete;
 ~Session();
 OwnedPublicForecast forecast(const ObservedActual&,const AcceptedCommandHistory&,
  const ProgressHistory&,const CurrentBoundaryExpectation&,const std::vector<NominalControl>&);
 const NativeMetadata& verifiedMetadata() const;
 void verifyTermination();
 bool terminationVerified() const;
 const std::string& terminationFailure() const;
 Count cumulativeCharges() const;
 private:
 std::shared_ptr<detail::SessionStorage> storage_;
};
}
