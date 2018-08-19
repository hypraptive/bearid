#
# This is a CMake makefile.  You can find the cmake utility and
# information about it at http://www.cmake.org
#


cmake_minimum_required(VERSION 2.8.4)

PROJECT(examples)

if (NOT DEFINED DLIB_PATH)
   set(DLIB_PATH "..")
endif()

include(${DLIB_PATH}/dlib/cmake)


# Since there are a lot of examples I'm going to use a macro to simply this
# CMakeLists.txt file.  However, usually you will create only one executable in
# your cmake projects and use the syntax shown above.
MACRO(add_example name)
   ADD_EXECUTABLE(${name} ${name}.cpp)
   TARGET_LINK_LIBRARIES(${name} dlib )
ENDMACRO()

# if an example requires GUI, call this macro to check DLIB_NO_GUI_SUPPORT to include or exclude
MACRO(add_gui_example name)
   if (DLIB_NO_GUI_SUPPORT)
      message("No GUI support, so we won't build the ${name} example.")
   else()
      add_example(${name})
   endif()
ENDMACRO()

# The deep learning toolkit requires a compiler with essentially complete C++11
# support.  However, versions of Visual Studio prior to October 2016 didn't
# provide enough C++11 support to compile the DNN tooling, but were good enough
# to compile the rest of dlib.
find_package(Boost COMPONENTS filesystem system)
if (Boost_FOUND)
  include_directories(${Boost_INCLUDE_DIRS})
  ADD_EXECUTABLE(bearface bearface.cpp)
  ADD_LIBRARY (bearlib find_faces.cpp)
  TARGET_LINK_LIBRARIES(bearface dlib bearlib ${Boost_LIBRARIES} )
  ADD_EXECUTABLE(bearchip bearchip.cpp)
  TARGET_LINK_LIBRARIES(bearchip dlib ${Boost_LIBRARIES} )
  ADD_EXECUTABLE(bearembed bearembed.cpp)
  TARGET_LINK_LIBRARIES(bearembed dlib ${Boost_LIBRARIES} )
  ADD_EXECUTABLE(bearsvm bearsvm.cpp)
  TARGET_LINK_LIBRARIES(bearsvm dlib ${Boost_LIBRARIES} )
  ADD_EXECUTABLE(bearid bearid.cpp)
  TARGET_LINK_LIBRARIES(bearid dlib ${Boost_LIBRARIES} )
  find_package(OpenCV)
  if (OpenCV_FOUND)
     include_directories(${OpenCV_INCLUDE_DIRS})
     ADD_EXECUTABLE(bearfacechip bearfacechip.cpp)
     TARGET_LINK_LIBRARIES(bearfacechip dlib ${Boost_LIBRARIES} ${OpenCV_LIBS} )
  else()
     message("OpenCV not found, so we won't build the bearchip.")
  endif()
else()
  message("No Boost Support, can't build")
endif()
