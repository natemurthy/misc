set(LIBCONTAINER_SRC
    containers.hpp
    containers.cpp
)

# Declare the library
add_library(libcontainer STATIC ${LIBCONTAINER_SRC})

target_link_libraries(libcontainer)

# Specify here the include directories exported
# by this library
target_include_directories(libcontainer PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
