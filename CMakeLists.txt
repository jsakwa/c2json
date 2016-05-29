set(LLVM_LINK_COMPONENTS support)
set(LLVM_USED_LIBS clangTooling clangBasic clangAST)

add_clang_executable(c2json c2json.cpp)

target_link_libraries(c2json
  clangTooling
  clangBasic
  clangASTMatchers
  )
  
set_target_properties(c2json PROPERTIES 
    OUTPUT_NAME c2json
)
  
add_custom_command(TARGET c2json
                   POST_BUILD
                   COMMAND ${CMAKE_COMMAND} 
                   -DC2JSON_PATH=$<TARGET_FILE:c2json>
                   -DINPUT_PATH=${CMAKE_CURRENT_SOURCE_DIR}/test-inputs
                   -DOUTPUT_PATH=${CMAKE_CURRENT_SOURCE_DIR}/test-outputs
                   -P ${CMAKE_CURRENT_SOURCE_DIR}/PrepareRunTest.cmake
                   )