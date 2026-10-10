#pragma once
#include "bootstrap_observer.hpp"
#include <filesystem>
#include <functional>
#include <openssl/evp.h>
#include <cstdint>
namespace phase5_first_cycle_v1 {
struct FileReceipt {std::string file,role,sha256,error;std::uint64_t bytes=0;bool complete=false,created=false,hash_valid=false;};
class BinaryFile final {
 public:
  void u64(std::uint64_t);void number(double);void text(const std::string&);
  void matrix(const Eigen::MatrixXd&);void vector(const Eigen::VectorXd&);
  void state(const phase5_public_coupled_augmented::State&);
  void state(const live::State30&);
 private:
  int fd_;EVP_MD_CTX* hash_;FileReceipt& receipt_;std::uint64_t& total_;std::uint64_t limit_;
  BinaryFile(int,EVP_MD_CTX*,FileReceipt&,std::uint64_t&,std::uint64_t);
  void bytes(const void*,std::size_t);friend class Evidence;
};
class Evidence final {
 public:
  explicit Evidence(const std::string& fresh_directory);
  void write(const std::string& file,const std::string& role,const std::function<void(BinaryFile&)>&);
  void snapshot(const std::string& file,const Snapshot&);
  void modelOpen(const live::ModelOpenOutcome&);
  void rawForecast(const live::OwnedPublicForecast&); // Must finish before adapter entry.
  void integration(const bridge::Outcome&);
  void candidate(const bridge::CandidateOutcome&);
  void bootstrap(const BootstrapFacts&);
  void finish(const std::string& stage,const std::string& error,bool same_boundary);
 private:
  std::filesystem::path dir_;std::vector<FileReceipt> receipts_;std::uint64_t total_=0;
};
}
