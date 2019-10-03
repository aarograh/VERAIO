"List of VIM special characters for reference.

"------- Input File Mappings and abbreviations --------
"++++++ functions
"quick comment out line

setlocal completefunc=verainputcomplete#CompleteCards
"This is the max size of the preview window
setlocal previewheight=10
"setlocal completeopt="menu,preview"

"The autocompletion hotkey
inoremap <TAB><TAB>     <C-X><C-U>
"Hotkey to close the preview window
inoremap <TAB><ESC>     <ESC><C-W><C-K>:q<CR>i
nnoremap <TAB><ESC>     <C-W><C-K>:q<CR>

"Hotkey to scroll in the preview window
inoremap <C-UP>         <ESC><C-W><C-K><UP><C-W><C-W>i
inoremap <C-DOWN>       <ESC><C-W><C-K><DOWN><C-W><C-W>i
nnoremap <C-UP>         <C-W><C-K><UP><C-W><C-W>
nnoremap <C-DOWN>       <C-W><C-K><DOWN><C-W><C-W>
inoremap <C-PAGEUP>     <ESC><C-W><C-K><PAGEUP><C-W><C-W>i
inoremap <C-PAGEDOWN>   <ESC><C-W><C-K><PAGEDOWN><C-W><C-W>i
nnoremap <C-PAGEUP>     <C-W><C-K><PAGEUP><C-W><C-W>
nnoremap <C-PAGEDOWN>   <C-W><C-K><PAGEDOWN><C-W><C-W>

