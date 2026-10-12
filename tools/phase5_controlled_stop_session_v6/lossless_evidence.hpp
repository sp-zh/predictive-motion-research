#pragma once
#include "runtime_observer.hpp"
#include "integrated_horizon_qp.hpp"
namespace phase5_active_evidence_v1 {namespace live=phase5_active_session_v1;namespace bridge=phase5_active_session_qp_v1;using Snapshot=phase5_active_session_runtime_v1::Snapshot;using BootstrapFacts=phase5_active_session_runtime_v1::NativeFacts;}
#include <filesystem>
#include <functional>
#include <openssl/evp.h>
#include <cstdint>
#include <array>
#include "lossless_stream_storage_v3.hpp"
namespace phase5_active_evidence_v1 {
struct FileReceipt {std::string file,role,sha256,error;std::uint64_t bytes=0;bool complete=false,created=false,hash_valid=false;std::string codec="RAW_V1",raw_sha256;std::uint64_t raw_bytes=0,zlib_allocation_peak=0;bool storage_stream_complete=false,raw_hash_valid=false,compressor_input_hash_valid=false;};
class BinaryFile final {
 public:
  void u64(std::uint64_t);void number(double);void text(const std::string&);
  void matrix(const Eigen::MatrixXd&);void vector(const Eigen::VectorXd&);
  void state(const phase5_public_coupled_augmented::State&);
  void state(const live::State30&);
 private:
  std::array<unsigned char,65536> buffer_{};std::size_t buffered_=0;bool flush_failed_=false;
  void flush();void writeStored(const unsigned char*,std::size_t);void closeStream();void updateRawReceipt();
  phase5_lossless_stream_storage_v3::StoredBudget* storage_=nullptr;std::unique_ptr<phase5_lossless_stream_storage_v3::Gzip> gzip_;
  int fd_;EVP_MD_CTX* hash_;FileReceipt& receipt_;std::uint64_t& total_;std::uint64_t limit_;phase5_dynamic_cycle_support_v1::Ledger* ledger_;
  BinaryFile(int,EVP_MD_CTX*,FileReceipt&,std::uint64_t&,std::uint64_t,phase5_dynamic_cycle_support_v1::Ledger*,phase5_lossless_stream_storage_v3::StoredBudget*);
  void bytes(const void*,std::size_t);friend class Evidence;
};
class Evidence final {
 public:
  explicit Evidence(const std::string& fresh_directory,phase5_dynamic_cycle_support_v1::Ledger* ledger=nullptr,phase5_lossless_stream_storage_v3::StoredBudget* storage=nullptr);
  void write(const std::string& file,const std::string& role,const std::function<void(BinaryFile&)>&);
  void snapshot(const std::string& file,const Snapshot&);
  void modelOpen(const live::Session&);
 void candidateValue(const live::OwnedCandidateValue&);
  void rawForecast(const live::OwnedPublicForecast&); // Must finish before adapter entry.
  void integration(const bridge::Outcome&);
  void candidate(const bridge::CandidateOutcome&);
  void bootstrap(const BootstrapFacts&);
 void warmup(const phase5_active_session_runtime_v1::WarmupOutcome&);
  void finish(const std::string& stage,const std::string& error,bool same_boundary);
 private:
  std::filesystem::path dir_;std::vector<FileReceipt> receipts_;std::uint64_t total_=0;phase5_dynamic_cycle_support_v1::Ledger* ledger_;phase5_lossless_stream_storage_v3::StoredBudget* storage_=nullptr;
};
}
