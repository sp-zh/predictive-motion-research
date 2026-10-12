#pragma once
#include <memory>
#include <stdexcept>
namespace phase5_designated_owner_v1 {
// Identity codec only. Runtime supplies actual private Session shared storage;
// arbitrary public use of this codec never creates a Session or permit.
class Binding final {std::weak_ptr<const void> owner_;bool bound_=false;public:
 void bind(const std::shared_ptr<const void>& owner){if(bound_||!owner)throw std::invalid_argument("one nonempty designated shared owner binding");owner_=owner;bound_=true;}
 bool matches(const std::shared_ptr<const void>& supplied)const noexcept {auto actual=owner_.lock();return bound_&&actual&&supplied&&!actual.owner_before(supplied)&&!supplied.owner_before(actual);}
 bool bound()const noexcept{return bound_;}
};
}
