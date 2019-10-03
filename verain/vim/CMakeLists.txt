TRIBITS_COPY_FILES_TO_BINARY_DIR(
  veravim_config
  SOURCE_FILES
    autoload
    ftplugin/verainput.vim
    syntax
    scripts.vim
)
CONFIGURE_FILE(
  ${CMAKE_CURRENT_SOURCE_DIR}/vimrc.in
  ${CMAKE_CURRENT_BINARY_DIR}/vimrc
)

ASSERT_DEFINED(PYTHON_EXECUTABLE)
ADD_CUSTOM_TARGET(
  VERAIn_veravim
  ALL
  DEPENDS VERAIn_veravim_config
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/VERAVim.py
  BYPRODUCTS
    "syntax/verainput.vim"
    "autoload/verainputcomplete.vim"
)

INSTALL(
  FILES
    ${CMAKE_CURRENT_BINARY_DIR}/scripts.vim
    ${CMAKE_CURRENT_BINARY_DIR}/vimrc
  DESTINATION "share/VERAIn/vim"
  COMPONENT ${PACKAGE_NAME}
)
INSTALL(
  FILES ${CMAKE_CURRENT_BINARY_DIR}/ftplugin/verainput.vim
  DESTINATION "share/VERAIn/vim/ftplugin"
  COMPONENT ${PACKAGE_NAME}
)
INSTALL(
  FILES ${CMAKE_CURRENT_BINARY_DIR}/syntax/verainput.vim
  DESTINATION "share/VERAIn/vim/syntax"
  COMPONENT ${PACKAGE_NAME}
)
INSTALL(
  FILES ${CMAKE_CURRENT_BINARY_DIR}/autoload/verainputcomplete.vim
  DESTINATION "share/VERAIn/vim/autoload"
  COMPONENT ${PACKAGE_NAME}
)
INSTALL(
  FILES ${CMAKE_CURRENT_SOURCE_DIR}/README.md
  DESTINATION "share/VERAIn/doc/"
  RENAME "README.VERAVim.md"
  COMPONENT ${PACKAGE_NAME}
)
