# VERAVim

## Minimum Requirements
VIM v7.4

## Installation
### Under VERA
With a standard VERA installation everything is handled by the `<VERA_INSTALL>/load_env.sh` script.
Simply source this script prior to opening a VERA input in vim.


### Outside VERA
If you happen to be using VERAIn oustide of VERA, you can configure VIM to use VERAVIM by
defining the following shell variable.
```
VIMINIT="set runtimepath+=@CMAKE_INSTALL_PREFIX@/share/VERAIn/vim|:source @CMAKE_INSTALL_PREFIX@/share/VERAIn/vim/vimrc"
```
in bash this is:
```
export VIMINIT="set runtimepath+=@CMAKE_INSTALL_PREFIX@/share/VERAIn/vim|:source @CMAKE_INSTALL_PREFIX@/share/VERAIn/vim/vimrc"
```
This can be done from the command line, through environment-modules, or in a login script.


## Usage
When you have opened a VERA input in VIM with the VERAVim plugin loaded you will note that there is syntax highlighting.
Additionally, you can
- "tab-complete" a input or see a list of available inputs within each block by pressing the `<TAB>` key twice in insert mode.
  - This also opens a help window at the top with the input's documentation.
  - The arrow keys scroll through the pop-up menu.
  - Pressing any key inserts the highlighted input from the menu, closes the menu,  and continues in insert mode.
  - Pressing `<ESC>` inserts the highlighted input, closes the menu, and returns to command mode.
- see the documentation on the current highlighted input.
- scroll in the help window by holding down `<CTRL>` and pressing the arrow keys.
- close the help window by pressing `<TAB>` then `<ESC>`.


## Troubleshooting
If you experience irregular behavior when working in VIM, please report this to `casl-support@ornl.gov`
and clear the `VIMINIT` variable. In bash this would be:
```
unset VIMINIT
```
