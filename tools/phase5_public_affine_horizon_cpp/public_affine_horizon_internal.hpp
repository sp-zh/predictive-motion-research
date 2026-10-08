#pragma once
#include "public_affine_horizon.hpp"
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
namespace phase5_public_affine_horizon::detail {
inline void require(bool v,const std::string& s){if(!v)throw std::invalid_argument(s);}
inline std::size_t add(std::size_t a,std::size_t b){require(b<=SIZE_MAX-a,"size addition overflow");return a+b;}
inline std::size_t mul(std::size_t a,std::size_t b){require(a==0||b<=SIZE_MAX/a,"size multiplication overflow");return a*b;}
void fixed(const Limits&);
void finite(const Matrix&); void finite(const Vector&);
Matrix zeros(std::size_t,std::size_t,ProblemBudget&);
Vector zeros(std::size_t,ProblemBudget&);
Matrix product(const Matrix&,const Matrix&,ProblemBudget&);
Vector product(const Matrix&,const Vector&,ProblemBudget&);
Matrix plus(const Matrix&,const Matrix&,ProblemBudget&);
Vector plus(const Vector&,const Vector&,ProblemBudget&);
double dot(const Vector&,const Vector&);
bool exact(const Vector&,const Vector&);
double residual(const Matrix&,const Matrix&,const Vector&,const Vector&,const Vector&,const Vector&,const Limits&,ProblemBudget&);
}
