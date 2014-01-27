!--------------------------------------------------------------------------------
!  Program to diff two VERA HDF output files
!
!  Copyright Core Physics, Inc.
!  9/6/2013
!
!  Right now, we are just performing a simple diff on eigenvalues with a
!  tolerance of 10 pcm.
!  This will be modifed in the future to check other parameters as well.
!
!  2014/01/27 - read boron coparison if dataset is present on file
!
!--------------------------------------------------------------------------------
      program veradiff
      use  hdf5
      implicit none

      character(len=250) :: fname1, fname2
      character(len=80)  :: dataset
      integer            :: iargs

      integer(hid_t)     :: file_id1, file_id2
      integer            :: ierror
      integer            :: nfail

      logical            :: ifxst

      real(8)            :: boron1, boron2
      real(8)            :: bordiff
      real(8)            :: bortol=1.0d0   ! boron tolerance (ppm)

      real(8)            :: xkeff1, xkeff2
      real(8)            :: xkdiff
      real(8)            :: xktol=10.0d0   ! eigenvalue tolerance (pcm)

      ierror=0
      fname1=' '
      fname2=' '

      boron1=-9999.0d0    ! large negative number if dataset not present
      boron2=-9999.0d0    ! large negative number if dataset not present

      xkeff1=0.0d0
      xkeff2=0.0d0

      nfail=0    ! number of test failures

!----------------------------------------------------------------------
!  Read in arguments from command line
!----------------------------------------------------------------------

      iargs = command_argument_count()
      if (iargs.lt.2) then
        write (*,*) 'usage:  veradiff.exe [file1] [file2]'
        nfail=nfail+1
        goto 900
      endif

      call get_command_argument(1,fname1)
      call get_command_argument(2,fname2)

      write (*,'(2a)') 'reading h5 file: ', trim(fname1)
      inquire(file=fname1, exist=ifxst)
      if (.not.ifxst) then
        write (*,*) 'ERROR: input file ',trim(fname1),' does not exist'
        nfail=nfail+1
        goto 900
      endif

      write (*,'(2a)') 'reading h5 file: ', trim(fname2)
      inquire(file=fname2, exist=ifxst)
      if (.not.ifxst) then
        write (*,*) 'ERROR: input file ',trim(fname2),' does not exist'
        nfail=nfail+1
        goto 900
      endif

!--------------------------------------------------------------------------------
! Initialize HDF and open files
!--------------------------------------------------------------------------------

!--- initialize fortran interface

      call h5open_f(ierror)      ! NOTE: THIS IS REQUIRED

!--- open file1

      call h5fopen_f (fname1, H5F_ACC_RDWR_F, file_id1, ierror)
      if (ierror<0) then
        write (*,'(3a)') 'ERROR: H5 input file ',trim(fname1),' could not be opened'
        nfail=nfail+1
        goto 900
      endif

!--- open file2

      call h5fopen_f (fname2, H5F_ACC_RDWR_F, file_id2, ierror)
      if (ierror<0) then
        write (*,'(3a)') 'ERROR: H5 input file ',trim(fname2),' could not be opened'
        nfail=nfail+1
        goto 900
      endif

!--------------------------------------------------------------------------------
! Read Eigenvalue and other scalers
!--------------------------------------------------------------------------------

!--- boron

      dataset='boron'    ! 'boron_conc' for some versions of Insilico
      call h5lexists_f(file_id1, dataset, ifxst, ierror)
      if (ifxst) call read_double(file_id1, dataset, boron1)
      call h5lexists_f(file_id2, dataset, ifxst, ierror)
      if (ifxst) call read_double(file_id2, dataset, boron2)

      if (boron1.gt.-1000.0d0 .and. boron2.gt.-1000.0d0) then
        bordiff=(boron2-boron1)
        write (*,'(a, f12.2)')   ' boron1 =', boron1
        write (*,'(a, f12.2)')   ' boron2 =', boron2
        write (*,'(a, f12.2,a)') ' diff   =', bordiff,' ppm'
        write (*,'(a, f12.2,a)') ' tol    =', bortol ,' ppm'
        if (abs(bordiff).lt.bortol) then
          write (*,*) 'PASS - boron difference is less than tolerance'
        else
          nfail=nfail+1
          write (*,*) 'FAIL - boron difference exceeds tolerance'
        endif
      else
        write (*,'(a)') 'No boron comparison performed - at least one file missing boron'
      endif

!--- eigenvalue
 

      dataset='keff'
      call h5lexists_f(file_id1, dataset, ifxst, ierror)
      if (ifxst) then
        call read_double(file_id1, dataset, xkeff1)
      else
        nfail=nfail+1
        write (*,*) 'FAIL - keff dataset does not exist on file'
      endif

      call h5lexists_f(file_id2, dataset, ifxst, ierror)
      if (ifxst) then
        call read_double(file_id2, dataset, xkeff2)
      else
        nfail=nfail+1
        write (*,*) 'FAIL - keff dataset does not exist on file'
      endif

      xkdiff=(xkeff2-xkeff1)*1.0d5

      write (*,'(a, f12.7)')   ' keff1  =', xkeff1
      write (*,'(a, f12.7)')   ' keff2  =', xkeff2
      write (*,'(a, f12.2,a)') ' diff   =', xkdiff,' pcm'
      write (*,'(a, f12.2,a)') ' tol    =', xktol ,' pcm'

      if (abs(xkdiff).lt.xktol) then
        write (*,*) 'PASS - eigenvalue difference is less than tolerance'
      else
        nfail=nfail+1
        write (*,*) 'FAIL - eigenvalue difference exceeds tolerance'
      endif

!--------------------------------------------------------------------------------
! Read pin powers
!--------------------------------------------------------------------------------

! Note: power array is allocated in subroutine

!!    dataset='pin_powers'
!!    call h5info(file_id, dataset, itype, ndim, idim)
!!    if (ndim.ne.4) stop 'invalid dimensions in core_map'
!!    npin =idim(1)
!!    kd   =idim(3)
!!    nassm=idim(4)
!!    if (idim(1).ne.idim(2)) stop 'invalid npin in read_power'
!!    write (*,*) '   npin ', npin
!!    write (*,*) '   kd   ', kd
!!    write (*,*) '   nassm', nassm
!!    allocate (power(npin, npin, kd, nassm))

!!    call read_double4d(file_id, dataset, npin, npin, kd, nassm, power)

!!    if (naxial-1.ne.kd) then
!!      stop 'mismatch found between axial levels in input and number of levels of output'
!!    endif

!--------------------------------------------------------------------------------
! Close File
!--------------------------------------------------------------------------------
      call h5fclose_f(file_id1, ierror)
      call h5fclose_f(file_id2, ierror)

!--------------------------------------------------------------------------------
! Print Results
!--------------------------------------------------------------------------------

  900 continue

      if (nfail.gt.0) call exit(nfail)    ! return error code

      end program
!=======================================================================
!
!  Subroutine to read double precision scalar from HDF5 file
!
!=======================================================================
      subroutine read_double(file_id, dataset, xvar)
      use  hdf5
      implicit none

      integer(hid_t),   intent(in) :: file_id
      character(len=*), intent(in) :: dataset
      real(8),          intent(out):: xvar

!--- local

      integer(hid_t)     :: dset_id
      integer(hid_t)     :: ispace_id
      integer            :: ierror
      integer            :: maxndim

      integer, parameter :: max_dimen=2     ! maximum number of dimensions allowed

      integer(hsize_t)   :: h_dims(max_dimen)
      integer(hsize_t)   :: h_maxdims(max_dimen)

      ierror=0
      xvar=-1.0d0    ! init

!--- Read double precision scalar

!--- open a dataset and dataspace

      write (*,'(1x,2a)') 'reading dataset: ', trim(dataset)

      call h5dopen_f(file_id, dataset, dset_id, ierror)
      if (ierror.lt.0) then
        write(*,'(3a)')   'error: data set ',trim(dataset), ' could not be opened'
        write(*,'(a,i8)') 'error code ', ierror
        return
      endif

      call h5dget_space_f(dset_id, ispace_id, ierror)       !Assign a dataspace based on the dataset
      if (ierror.ne.0) then
        write (*,*) 'error: h5dget_space_f ', ierror
        stop        'error: h5dget_space_f'
      endif

! Determine number of discrete subunits for each dimensions
      h_dims(:)=0
      h_maxdims(:)=0
      call h5sget_simple_extent_dims_f(ispace_id, h_dims, h_maxdims, ierror)
      if (ierror.lt.0) then    ! returns rank in ierror
        write (*,*) 'error: h5sget_simple_extent_dims_f ', ierror
        stop        'error: h5sget_simple_extent_dims_f'
      endif
      maxndim=ierror

      if (maxndim.gt.max_dimen) stop 'maximum dimensions exceeded'
      if (maxndim.ne.1) stop 'invalid number of dimensions'

!!    if (ifdebug) then
!!      write (*,110) trim(dataset)
!!      write (*,115) 'number of dimensions: ', maxndim
!!      write (*,115) 'dimensions    : ', h_dims(1:maxndim)
!!      write (*,115) 'dimensions max: ', h_maxdims(1:maxndim)
!!    endif
!!110 format (/,' dataset : ', a)
!!115 format (1x,a,20i4)

! Read data from dataset
      call h5dread_f(dset_id, H5T_NATIVE_DOUBLE, xvar, h_dims, ierror)
      if (ierror.ne.0) then
        write(*,*) 'error: h5dread_f reading  data set ',trim(dataset)
        stop
      endif

! Close dataspace and dataset

      call h5sclose_f(ispace_id, ierror)
      call h5dclose_f(dset_id, ierror)

      return
      end subroutine read_double
!=======================================================================
