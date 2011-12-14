
module forpl

  
  use iso_c_binding ,only : c_int,c_double,c_char,c_bool,c_ptr,c_long,c_float
  use ForTrilinos_enums
  use ForTrilinos_enum_wrappers
  implicit none   ! Prevent implicit typing
  

  interface


     function Teuchos_ParameterList_Create (  ) result(that) &
          bind(C,name='Teuchos_ParameterList_Create')
       import :: FT_Teuchos_ParameterList_ID_t
       type(FT_Teuchos_ParameterList_ID_t) :: that
     end function


     function Teuchos_ParameterList_set_int ( selfID, name, value, docString ) result(that) &
          bind(C,name='Teuchos_ParameterList_set_int')
       import :: FT_Teuchos_ParameterList_ID_t ,c_char ,c_int
       
       type(FT_Teuchos_ParameterList_ID_t)                                  :: that
       type(FT_Teuchos_ParameterList_ID_t),intent(in)   ,value              :: selfID
       character(kind=c_char)             ,intent(in)         ,dimension(*) :: name
       integer(c_int)                     ,intent(in)   ,value              :: value
       character(kind=c_char)             ,intent(in)         ,dimension(*) :: docString
     end function Teuchos_ParameterList_set_int
     

     function Teuchos_ParameterList_get_int ( selfID, name ) result(that) &
          bind(C,name='Teuchos_ParameterList_get_int')
       import :: c_int ,FT_Teuchos_ParameterList_ID_t ,c_char
       
       integer(c_int)                                                       :: that
       type(FT_Teuchos_ParameterList_ID_t),intent(in)   ,value              :: selfID
       character(kind=c_char)             ,intent(in)         ,dimension(*) :: name
     end function Teuchos_ParameterList_get_int

  end interface

  contains


    subroutine Teuchos_ParameterList_set_int2 ( selfID, name, value, docString )
      
      type(FT_Teuchos_ParameterList_ID_t)                                  :: that
      type(FT_Teuchos_ParameterList_ID_t),intent(in)   ,value              :: selfID
      character(kind=c_char)             ,intent(in)         ,dimension(*) :: name
      integer(c_int)                     ,intent(in)   ,value              :: value
      character(kind=c_char)             ,intent(in)         ,dimension(*) :: docString
      
      that = Teuchos_ParameterList_set_int(selfID, name, value, docString)
      
    end subroutine Teuchos_ParameterList_set_int2
    
    
end module forpl
