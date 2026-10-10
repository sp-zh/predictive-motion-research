// Source proposal only. Future real reads limited to a separately installed/frozen synthetic fixture directory.
#include "foundation.hpp"
#include "identity_expected_v1.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
#ifndef IDENTITY_FIXTURE_ROOT
#error "Future reviewed compile must pin the same absolute fixture root as explicit runtime argv"
#endif
namespace p=phase5_public_live_affine_v2;namespace e=identity_expected;
namespace {
std::string root;std::size_t total=0,identities=0,ranges=0;
void require(bool x,const char* m){if(!x)throw std::runtime_error(m);}
const e::Fixture& fixture(const char* name){for(const auto& x:e::fixtures)if(std::string(x.name)==name)return x;throw std::runtime_error("unlisted fixture");}
std::string path(const char* name){(void)fixture(name);return root+"/"+name;}
p::FileIdentity observe(const std::string& name,const std::string& digest){require(total<e::target_entries&&identities<e::identity_entries,"identity target cap");++total;++identities;return p::observePinnedFile(name,digest);}
p::StaticDomainRanges load(const char* name){require(total<e::target_entries&&ranges<e::range_entries,"range target cap");const auto& f=fixture(name);++total;++ranges;return p::loadPinnedStaticRanges(path(name),f.sha);}
void identity(const p::FileIdentity& value,const char* name){const auto& f=fixture(name);require(value.path==path(name)&&value.bytes==f.bytes&&value.sha256==f.sha,"actual fileidentity mismatch");}
void limits(const p::StaticDomainRanges& value,const char* name){identity(value.constantsIdentity(),name);for(std::size_t j=0;j<7;++j)require(value.qLower()[j]==e::q_lower[j]&&value.qUpper()[j]==e::q_upper[j]&&value.cLower()[j]==e::c_lower[j]&&value.cUpper()[j]==e::c_upper[j],"literal28 range getters mismatch");}
template<class F>void invalid(F f,const char* expected){bool caught=false;try{f();}catch(const std::invalid_argument& x){caught=true;require(std::string(x.what())==expected,"wrong stable refusal message");}require(caught,"required invalid_argument missing");}
void plain(){const auto& f=fixture("identity_plain.txt");identity(observe(path(f.name),f.sha),f.name);}
void yamlBytes(){const auto& f=fixture("ranges_valid.yaml");identity(observe(path(f.name),f.sha),f.name);}
void validRanges(){const auto value=load("ranges_valid.yaml");limits(value,"ranges_valid.yaml");}
void extraKey(){const auto value=load("ranges_extra_key.yaml");limits(value,"ranges_extra_key.yaml");}
void shaSyntax(){const auto file=path("identity_plain.txt");invalid([&]{(void)observe(file,"");},"SHA256 must contain64 lowercase hexadecimal characters");invalid([&]{(void)observe(file,std::string(63,'0'));},"SHA256 must contain64 lowercase hexadecimal characters");invalid([&]{(void)observe(file,std::string(64,'A'));},"SHA256 must use lowercase hexadecimal");invalid([&]{(void)observe(file,std::string(64,'g'));},"SHA256 must use lowercase hexadecimal");}
void pathSyntax(){const auto& f=fixture("identity_plain.txt");invalid([&]{(void)observe("",f.sha);},"bounded file path without embedded NUL required");invalid([&]{(void)observe(std::string(4097,'x'),f.sha);},"bounded file path without embedded NUL required");const auto nul=path(f.name)+std::string(1,'\0');invalid([&]{(void)observe(nul,f.sha);},"bounded file path without embedded NUL required");}
void shaBeforePath(){invalid([&]{(void)observe("","");},"SHA256 must contain64 lowercase hexadecimal characters");}
void mismatch(){invalid([&]{(void)observe(path("identity_plain.txt"),e::zero_sha);},"identity input SHA256 mismatch");}
void empty(){const auto& f=fixture("identity_empty.txt");invalid([&]{(void)observe(path(f.name),f.sha);},"identity input byte cap exceeded or empty file");}
void missing(){const auto& f=fixture("identity_plain.txt");bool caught=false;try{(void)observe(root+"/declared_missing.txt",f.sha);}catch(const std::runtime_error& x){caught=true;require(std::string(x.what()).rfind("cannot open identity input: ",0)==0,"wrong open-error category prefix");}require(caught,"required missing-file open failure absent");}
void directory(){const auto& f=fixture("identity_plain.txt");invalid([&]{(void)observe(root,f.sha);},"identity input must be a regular file");}
void rangeRefusal(const char* name,const char* message){invalid([&]{const auto value=load(name);(void)value;},message);}
}
int main(int argc,char** argv){try{require(argc==2,"exactly one frozen fixture-root argument required");root=argv[1];require(root==IDENTITY_FIXTURE_ROOT&&!root.empty()&&root[0]=='/'&&root.size()<=4096,"wrong frozen absolute fixture root");require(sizeof(e::fixtures)/sizeof(e::fixtures[0])==e::fixture_count&&e::fixture_count<=e::max_fixture_count,"fixed fixture count cap");std::size_t bytes=0;for(const auto& f:e::fixtures){require(f.bytes<=e::max_file_bytes,"fixed perfixture cap");bytes+=f.bytes;}require(bytes<=e::max_total_fixture_bytes,"fixed fixture aggregate cap");
struct Group{const char* id;void(*run)();const char* fixture;const char* refusal;std::size_t expected_entries;};const Group groups[]={
{"identity_plain_bytes",plain,nullptr,nullptr,1},{"identity_yaml_bytes",yamlBytes,nullptr,nullptr,1},{"ranges_valid_getters",validRanges,nullptr,nullptr,1},{"ranges_extra_key_allowed",extraKey,nullptr,nullptr,1},{"identity_sha_syntax_before_io",shaSyntax,nullptr,nullptr,4},{"identity_path_syntax_before_io",pathSyntax,nullptr,nullptr,3},{"identity_sha_before_bad_path",shaBeforePath,nullptr,nullptr,1},{"identity_digest_mismatch",mismatch,nullptr,nullptr,1},{"identity_empty_file",empty,nullptr,nullptr,1},{"identity_missing_file",missing,nullptr,nullptr,1},{"identity_directory_nonregular",directory,nullptr,nullptr,1},
{"range_nonmap",nullptr,"ranges_nonmap.yaml","static constants must be a keyed object",1},
{"range_duplicate_key",nullptr,"ranges_duplicate_key.yaml","duplicate static constants key",1},
{"range_joint13",nullptr,"ranges_joint13.yaml","static range/list roster mismatch",1},
{"range_control15",nullptr,"ranges_control15.yaml","static range/list roster mismatch",1},
{"range_joint_flags6",nullptr,"ranges_joint_flags6.yaml","static range/list roster mismatch",1},
{"range_control_flags8",nullptr,"ranges_control_flags8.yaml","static range/list roster mismatch",1},
{"range_joint_flag0",nullptr,"ranges_joint_flag0.yaml","fixed bounded FR3 joint and command profile required",1},
{"range_control_flag2",nullptr,"ranges_control_flag2.yaml","fixed bounded FR3 joint and command profile required",1},
{"range_nan",nullptr,"ranges_nan.yaml","finite ordered static ranges required",1},
{"range_positive_inf",nullptr,"ranges_positive_inf.yaml","finite ordered static ranges required",1},
{"range_negative_inf",nullptr,"ranges_negative_inf.yaml","finite ordered static ranges required",1},
{"range_reversed",nullptr,"ranges_reversed.yaml","finite ordered static ranges required",1},
{"range_equal",nullptr,"ranges_equal.yaml","finite ordered static ranges required",1},
};
std::size_t completed=0;for(const auto& g:groups){const auto before=total;if(g.run)g.run();else rangeRefusal(g.fixture,g.refusal);require(total-before==g.expected_entries,"group target entry mismatch");++completed;std::cout<<"PASS "<<g.id<<'\n';}require(completed==e::group_count&&total==e::target_entries&&identities==e::identity_entries&&ranges==e::range_entries,"fixed group/API count closure mismatch");std::cout<<"COMPLETE 24 identity/range groups; identity entries 14; range entries 15; total 29; no phase acceptance\n";return 0;}catch(const std::exception& x){std::cerr<<"FAIL "<<x.what()<<'\n';return 1;}}
