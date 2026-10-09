# Source-only chunk reader stat identifier repair

Reader::finish line84 declares `struct stat final{}`. The contextual class-head specifier `final` causes this declaration to be parsed as a local class definition rather than the intended stat variable; the actual GCC diagnostic reports the later identifier undeclared. The proposal renames the intended identifier to `after_stat`.

Exactly seven identifier tokens on one line change: one declaration and six same-variable uses. Reversing that token rename restores every original byte. File/FD regularity, link count, device/inode/size checks, complete SHA, EOF/EINTR behavior, budget accounting, failure messages, interfaces, numerical formulas and whitespace are untouched. The only matching declaration in the current namespace scan is the already identified one. No extra repair is proposed.

This packet is a static proposal only. No syntax fixture, compiler, configure/build, metadata query or project function was run. Canonical source, Dell readonly snapshot, old build trees and failures remain unchanged. Root is the sole importer and must independently review before/after/diff, then back up the code milestone. A new versioned source snapshot and separate configure/build dispatch are required for compilation validation. No old partial object is treated as fresh evidence. Phase5 is NOT_ACCEPTED; Phase6 is NOT_STARTED.
