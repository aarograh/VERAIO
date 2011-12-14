

subroutine test_forpl_set_get_int(verbose, result_flag_out)
  use iso_c_binding ,only : c_int, c_double, c_bool
  use forpl
  implicit none

  integer(c_bool), intent(in) :: verbose
  integer(c_int), intent(out) :: result_flag_out
  integer(c_int) myint1, myint2

  type(FT_Teuchos_ParameterList_ID_t) pl
  type(FT_Teuchos_ParameterList_ID_t) dummy

  result_flag_out = 0

  pl = Teuchos_ParameterList_Create()

  ! Call set int as a function
  dummy = Teuchos_ParameterList_set_int(pl, "my int 1", 5, "")
  myint1 = Teuchos_ParameterList_get_int(pl, "my int 1")
  if (verbose) then
    print *, "my int 1 = ", myint1
  end if
  if (myint1 .neqv. 5) then
    result_flag_out = 1
  end if

  ! Call set int as a subroutine
  call Teuchos_ParameterList_set_int2(pl, "my int 2", 6, "")
  myint2 = Teuchos_ParameterList_get_int(pl, "my int 2")
  if (verbose) then
    print *, "my int 2 = ", myint2
  end if
  if (myint2 .neqv. 6) then
    result_flag_out = 2
  end if

end subroutine
