#include <pybind11/pybind11.h>

namespace py = pybind11;

// Minimal test class
class MinimalEngine {
public:
    MinimalEngine() = default;
    
    std::string test() {
        return "Hello from C++ engine!";
    }
};

// PyBind11 module
PYBIND11_MODULE(enhanced_high_perf_engine, m) {
    py::class_<MinimalEngine>(m, "MinimalEngine")
        .def(py::init<>())
        .def("test", &MinimalEngine::test);
}
