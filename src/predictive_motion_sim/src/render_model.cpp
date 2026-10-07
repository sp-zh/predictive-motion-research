#include <GLFW/glfw3.h>

#include <fstream>
#include <iostream>
#include <vector>

#include "predictive_motion_sim/plant.hpp"
int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "Usage: render_model scene.xml snapshot.ppm\n";
    return 2;
  }
  try {
    predictive_motion::Plant p(argv[1]);
    if (!glfwInit()) throw std::runtime_error("GLFW initialization failed; GUI gate FAIL");
    GLFWwindow* window = glfwCreateWindow(800, 600, "Phase0 FR3 MuJoCo", nullptr, nullptr);
    if (!window) {
      glfwTerminate();
      throw std::runtime_error("No OpenGL window; GUI gate FAIL");
    }
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);
    mjvCamera cam;
    mjv_defaultCamera(&cam);
    cam.lookat[2] = 0.55;
    cam.distance = 2.0;
    cam.azimuth = 135;
    cam.elevation = -25;
    mjvOption opt;
    mjv_defaultOption(&opt);
    mjvScene scene;
    mjv_defaultScene(&scene);
    mjv_makeScene(p.model(), &scene, 2000);
    mjrContext context;
    mjr_defaultContext(&context);
    mjr_makeContext(p.model(), &context, mjFONTSCALE_100);
    int w = 0, h = 0;
    bool captured = false;
    for (int frame = 0; frame < 120 && !glfwWindowShouldClose(window); ++frame) {
      p.step();
      glfwGetFramebufferSize(window, &w, &h);
      mjrRect viewport{0, 0, w, h};
      mjv_updateScene(p.model(), p.data(), &opt, nullptr, &cam, mjCAT_ALL, &scene);
      mjr_render(viewport, &scene, &context);
      if (frame == 119) {
        std::vector<unsigned char> pixels(static_cast<size_t>(w * h * 3));
        mjr_readPixels(pixels.data(), nullptr, viewport, &context);
        std::ofstream out(argv[2], std::ios::binary);
        out << "P6\n" << w << " " << h << "\n255\n";
        for (int y = h - 1; y >= 0; --y)
          out.write(reinterpret_cast<char*>(pixels.data() + y * w * 3), w * 3);
        if (!out) throw std::runtime_error("Snapshot write failed");
        captured = true;
      }
      glfwSwapBuffers(window);
      glfwPollEvents();
    }
    mjr_freeContext(&context);
    mjv_freeScene(&scene);
    glfwDestroyWindow(window);
    glfwTerminate();
    if (!captured)
      throw std::runtime_error("Window closed before snapshot; visualization gate FAIL");
    std::cout << "GUI_RENDER_OK " << w << "x" << h << "\n";
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
