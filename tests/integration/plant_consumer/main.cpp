#include <iostream>
#include <predictive_motion_sim/plant.hpp>
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  predictive_motion::Plant plant(argv[1]);
  plant.step();
  std::cout << "STANDALONE_PLANT_OK time=" << plant.time() << '\n';
  return 0;
}
