#!/bin/bash

if [[ ${1} == "clean" ]]; then
    echo "clean build"
    rm -r ./workspace/build/* ./workspace/install/*
fi

# cp -p /aichallenge/workspace/src/aichallenge_system/autoware_overlay_rviz_plugin/src/speed_display_4digits.cpp /aichallenge/workspace/src/aichallenge_system/autoware_overlay_rviz_plugin/src/speed_display.cpp
cp -p /aichallenge/workspace/src/aichallenge_submit/simple_pure_pursuit/src/simple_pure_pursuit_isshy.cpp /aichallenge/workspace/src/aichallenge_submit/simple_pure_pursuit/src/simple_pure_pursuit.cpp
cp -p /aichallenge/workspace/src/aichallenge_submit/simple_pure_pursuit/include/simple_pure_pursuit/simple_pure_pursuit_isshy.hpp /aichallenge/workspace/src/aichallenge_submit/simple_pure_pursuit/include/simple_pure_pursuit/simple_pure_pursuit.hpp
cp -p /aichallenge/workspace/src/aichallenge_submit/aichallenge_submit_launch/launch/reference.launch_isshy.xml /aichallenge/workspace/src/aichallenge_submit/aichallenge_submit_launch/launch/reference.launch.xml

cd ./workspace || exit
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
