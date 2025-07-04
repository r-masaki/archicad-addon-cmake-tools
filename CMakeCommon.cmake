function (SetGlobalCompilerDefinitions acVersion addOnLanguage)

    if (WIN32)
        add_definitions (-DUNICODE -D_UNICODE)
    else ()
        add_definitions (-Dmacintosh=1)
        if (${acVersion} GREATER_EQUAL 26)
            set (CMAKE_OSX_ARCHITECTURES "x86_64;arm64" PARENT_SCOPE CACHE STRING "" FORCE)
        endif ()
    endif ()
    add_definitions (-DACExtension)

    if(NOT addOnLanguage)
        set(locLang "INT")
    else ()
        set(locLang ${addOnLanguage})
    endif ()

    set(locLangMacro "USE_${locLang}")
    add_definitions (-D${locLangMacro})

endfunction ()

function (SetCompilerOptions target acVersion)

    if (${acVersion} LESS 27)
        target_compile_features (${target} PUBLIC cxx_std_14)
    elseif (${acVersion} LESS 29)
        target_compile_features (${target} PUBLIC cxx_std_17)
    else ()
        target_compile_features (${target} PUBLIC cxx_std_20)
    endif ()

    target_compile_options (${target} PUBLIC "$<$<CONFIG:Debug>:-DDEBUG>")
    if (WIN32)
        target_compile_options (${target} PUBLIC /W4 /WX
            /Zc:wchar_t-
            /wd4499
            /wd4819
            /EHsc
            -D_CRT_SECURE_NO_WARNINGS
        )
    else ()
        target_compile_options (${target} PUBLIC -Wall -Wextra -Werror
            -fvisibility=hidden
            -Wno-multichar
            -Wno-ctor-dtor-privacy
            -Wno-invalid-offsetof
            -Wno-ignored-qualifiers
            -Wno-reorder
            -Wno-overloaded-virtual
            -Wno-unused-parameter
            -Wno-unused-value
            -Wno-unused-private-field
            -Wno-deprecated
            -Wno-unknown-pragmas
            -Wno-missing-braces
            -Wno-missing-field-initializers
            -Wno-non-c-typedef-for-linkage
            -Wno-uninitialized-const-reference
            -Wno-shorten-64-to-32
            -Wno-sign-compare
            -Wno-switch
        )
        if (${acVersion} LESS_EQUAL "24")
            target_compile_options (${target} PUBLIC -Wno-non-c-typedef-for-linkage)
        endif ()
    endif ()
    
endfunction ()

function (LinkGSLibrariesToProject acVersion devKitDir addOnName)

    if (WIN32)
        if (${acVersion} LESS 27)
            target_link_libraries (${addOnName}
                "$<$<CONFIG:Debug>:${devKitDir}/Lib/Win/ACAP_STATD.lib>"
                "$<$<CONFIG:Release>:${devKitDir}/Lib/Win/ACAP_STAT.lib>"
                "$<$<CONFIG:RelWithDebInfo>:${devKitDir}/Lib/Win/ACAP_STAT.lib>"
            )
        else ()
            target_link_libraries (${addOnName}
                "$<$<CONFIG:Debug>:${devKitDir}/Lib/ACAP_STATD.lib>"
                "$<$<CONFIG:Release>:${devKitDir}/Lib/ACAP_STAT.lib>"
                "$<$<CONFIG:RelWithDebInfo>:${devKitDir}/Lib/ACAP_STAT.lib>"
            )
        endif ()
    else ()
        find_library (CocoaFramework Cocoa)
        if (${acVersion} LESS 27)
            target_link_libraries (${addOnName}
                "${devKitDir}/Lib/Mactel/libACAP_STAT.a"
                ${CocoaFramework}
            )
        else ()
            target_link_libraries (${addOnName}
                "${devKitDir}/Lib/libACAP_STAT.a"
                ${CocoaFramework}
            )
        endif ()
    endif ()

    file (GLOB ModuleFolders ${devKitDir}/Modules/*)
    target_include_directories (${addOnName} PUBLIC ${ModuleFolders})
    if (WIN32)
        file (GLOB LibFilesInFolder ${devKitDir}/Modules/*/*/*.lib)
        target_link_libraries (${addOnName} ${LibFilesInFolder})
    else ()
        file (GLOB LibFilesInFolder
            ${devKitDir}/Frameworks/*.framework
            ${devKitDir}/Frameworks/*.dylib
        )
        target_link_libraries (${addOnName} ${LibFilesInFolder})
    endif ()

endfunction ()

function (GenerateAddOnProject acVersion devKitDir addOnName addOnSourcesFolder addOnResourcesFolder addOnLanguage additionalIncludeDirs)

    find_package (Python COMPONENTS Interpreter)

    set (ResourceObjectsDir ${CMAKE_BINARY_DIR}/ResourceObjects)
    set (ResourceStampFile "${ResourceObjectsDir}/AddOnResources.stamp")

    file (GLOB AddOnImageFiles CONFIGURE_DEPENDS
        ${addOnResourcesFolder}/RFIX/Images/*.svg
    )
    if (WIN32)
        file (GLOB AddOnResourceFiles CONFIGURE_DEPENDS
            ${addOnResourcesFolder}/R${addOnLanguage}/*.grc
            ${addOnResourcesFolder}/RFIX/*.grc
            ${addOnResourcesFolder}/RFIX.win/*.rc2
            ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/*.py
        )
    else ()
        file (GLOB AddOnResourceFiles CONFIGURE_DEPENDS
            ${addOnResourcesFolder}/R${addOnLanguage}/*.grc
            ${addOnResourcesFolder}/RFIX/*.grc
            ${addOnResourcesFolder}/RFIX.mac/*.plist
            ${addOnResourcesFolder}/RFIX.mac/*.xcconfig
            ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/*.py
        )
    endif ()

    get_filename_component (AddOnSourcesFolderAbsolute "${CMAKE_CURRENT_LIST_DIR}/${addOnSourcesFolder}" ABSOLUTE)
    get_filename_component (AddOnResourcesFolderAbsolute "${CMAKE_CURRENT_LIST_DIR}/${addOnResourcesFolder}" ABSOLUTE)
    if (WIN32)
        add_custom_command (
            OUTPUT ${ResourceStampFile}
            DEPENDS ${AddOnResourceFiles} ${AddOnImageFiles}
            COMMENT "Compiling resources..."
            COMMAND ${CMAKE_COMMAND} -E make_directory "${ResourceObjectsDir}"
            COMMAND ${Python_EXECUTABLE} "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/MakeACLib.py" "${addOnLanguage}"
            COMMAND ${Python_EXECUTABLE} "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/CompileResources.py" "${addOnLanguage}" "${devKitDir}" "${AddOnSourcesFolderAbsolute}" "${AddOnResourcesFolderAbsolute}" "${ResourceObjectsDir}" "${ResourceObjectsDir}/${addOnName}.res"
            COMMAND ${CMAKE_COMMAND} -E touch ${ResourceStampFile}
        )
    else ()

        add_custom_command (
            OUTPUT ${ResourceStampFile}
            DEPENDS ${AddOnResourceFiles} ${AddOnImageFiles}
            COMMENT "Compiling resources..."
            COMMAND ${CMAKE_COMMAND} -E make_directory "${ResourceObjectsDir}"
            COMMAND ${Python_EXECUTABLE} "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/MakeACLib.py" "${addOnLanguage}"
            COMMAND ${Python_EXECUTABLE} "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/CompileResources.py" "${addOnLanguage}" "${devKitDir}" "${AddOnSourcesFolderAbsolute}" "${AddOnResourcesFolderAbsolute}" "${ResourceObjectsDir}" "${CMAKE_BINARY_DIR}/$<CONFIG>/${addOnName}.bundle/Contents/Resources"
            COMMAND ${CMAKE_COMMAND} -E copy "${devKitDir}/Inc/PkgInfo" "${CMAKE_BINARY_DIR}/$<CONFIG>/${addOnName}.bundle/Contents/PkgInfo"
            COMMAND ${CMAKE_COMMAND} -E touch ${ResourceStampFile}
        )
    endif ()

    file (GLOB AddOnHeaderFiles CONFIGURE_DEPENDS
        ${addOnSourcesFolder}/*.h
        ${addOnSourcesFolder}/*.hpp
    )
    file (GLOB AddOnSourceFiles CONFIGURE_DEPENDS
        ${addOnSourcesFolder}/*.c
        ${addOnSourcesFolder}/*.cpp
    )
    set (
        AddOnFiles
        ${AddOnHeaderFiles}
        ${AddOnSourceFiles}
        ${AddOnImageFiles}
        ${AddOnResourceFiles}
        ${ResourceStampFile}
    )
    
    source_group ("Sources" FILES ${AddOnHeaderFiles} ${AddOnSourceFiles})
    source_group ("Images" FILES ${AddOnImageFiles})
    source_group ("Resources" FILES ${AddOnResourceFiles})
    if (WIN32)
        add_library (${addOnName} SHARED ${AddOnFiles})
    else ()
        add_library (${addOnName} MODULE ${AddOnFiles})
    endif ()

    set_target_properties (${addOnName} PROPERTIES OUTPUT_NAME ${addOnName})
    if (WIN32)
        set_target_properties (${addOnName} PROPERTIES SUFFIX ".apx")
        set_target_properties (${addOnName} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_$<CONFIG> "${CMAKE_BINARY_DIR}/$<CONFIG>")
        target_link_options (${addOnName} PUBLIC "${ResourceObjectsDir}/${addOnName}.res")
        target_link_options (${addOnName} PUBLIC /export:GetExportedFuncAddrs,@1 /export:SetImportedFuncAddrs,@2)
    else ()
        set_target_properties (${addOnName} PROPERTIES BUNDLE TRUE)
        set_target_properties (${addOnName} PROPERTIES MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_LIST_DIR}/${addOnResourcesFolder}/RFIX.mac/Info.plist")
        set_target_properties (${addOnName} PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/$<CONFIG>")
        set_target_properties(${addOnName} PROPERTIES
                                XCODE_ATTRIBUTE_CODE_SIGN_INJECT_BASE_ENTITLEMENTS "NO"
                                XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Manual"
                                XCODE_ATTRIBUTE_ENABLE_HARDENED_RUNTIME "YES"
                                XCODE_ATTRIBUTE_OTHER_CODE_SIGN_FLAGS "--timestamp --option=runtime"
                                )
    endif ()

    target_include_directories (${addOnName} PUBLIC
        ${addOnSourcesFolder}
        ${devKitDir}/Inc
    )

    if (NOT additionalIncludeDirs STREQUAL "")
        message(WARNING "Additional Include Dir = ${additionalIncludeDirs}")
        string(REPLACE " " ";" include_dirs ${additionalIncludeDirs})

        if (include_dirs)
            foreach (dir IN LISTS include_dirs)
                if (IS_DIRECTORY ${dir})
                    target_include_directories (${addOnName} PUBLIC ${dir})
                    message(WARNING "Directory ${dir} is a directory.")
    
                    file (GLOB subDirs ${dir}/*)
                    foreach (subDir ${subDirs})
                        if (IS_DIRECTORY ${subDir})
                            target_include_directories (${addOnName} PUBLIC ${subDir})
                            message(WARNING "Sub-directory ${subDir} is a directory.")
                        else ()
                            # message(WARNING "Sub-directory ${subDir} is not a directory.")
                        endif ()
                    endforeach ()
                else ()
                    # message(WARNING "Directory ${dir} is not a directory.")
                endif ()
            endforeach ()
        endif ()
    endif ()

    LinkGSLibrariesToProject (${acVersion} ${devKitDir} ${addOnName})

    set_source_files_properties (${AddOnSourceFiles} PROPERTIES LANGUAGE CXX)
    SetCompilerOptions (${addOnName} ${acVersion})
endfunction ()
