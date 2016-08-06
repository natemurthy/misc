set(MAIN_SRC 
  main.cpp
)

add_executable(my_app ${MAIN_SRC})

# Specify here the libraries this program depends on
target_link_libraries(my_app
  libcontainer
)


install(TARGETS my_app DESTINATION ${CMAKE_SOURCE_DIR}/bin)
