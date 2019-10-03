function! SetInputFileType()
  "count the number of matches for [CASEID]
  ":let n=[0] | bufdo %s/pattern\zs/\=map(n,'v:val+1')[1:]/ge
  "The variable is passed into the search, and it must be a list or
  "dictionary. If the search string is found, the variable is incremented
  "and returned.
  let isvera=[0] | %s/\[CASEID\]\zs/\=map(isvera,'v:val+1')[1:]/ge
  "echom "isvera[0]"
  let ismpact=[0] | %s/CASEID\zs/\=map(ismpact,'v:val+1')[1:]/ge
  if ismpact[0] == 0
    let ismpact=[0] | %s/mod_dim\zs/\=map(ismpact,'v:val+1')[1:]/ge
  endif

  if isvera[0] > 0
    set filetype=verainput
  elseif ismpact[0] > 0
    set filetype=mpactinput
  else
    set filetype=input
  endif

endfunction

au BufNewFile,BufRead *.inp call SetInputFileType()
au BufNewFile,BufRead *.ini set filetype=verainput
