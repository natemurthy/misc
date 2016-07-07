cmake_minimum_required(VERSION 2.8)

project(containers)

set(GCC_COVERAGE_COMPILE_FLAGS "-std=gnu++11")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${GCC_COVERAGE_COMPILE_FLAGS}")

enable_testing()

add_subdirectory(main)
add_subdirectory(test)
add_subdirectory(libcontainer)
