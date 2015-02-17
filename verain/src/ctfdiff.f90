   program ctfdiff
!=======================================================================
!
!  Program to compare two CTF HDF output file and print summary
!
!  Copyright (c) 2015 Core Physics, Inc.
!
!  Distributed under the MIT license.
!  See the LICENSE file in the main directory for details.
!
!  Main directory: https://github.com/palmtag/VERAout-tools/
!
!=======================================================================
!
!  This program is intended to be used in regressing testing
!
!  2015/02/17 - original program based on VERADiff      - see #3623
!
!
!-----------------------------------------------------------------------
      use hdf5
      implicit none

      character(len=250) :: fname1, fname2   ! HDF file names
      integer            :: iargs            ! number of command line arguments

      integer(hid_t)     :: file_id1, file_id2  ! HDF file id's
      integer            :: ierror
      integer            :: nfail            ! number of diff failures
      integer            :: nstate           ! statepoint number

      logical            :: ifxst

      character(len=10) :: group_name

      ierror=0
      fname1=' '
      fname2=' '

      nfail=0    ! number of test failures

!----------------------------------------------------------------------
!  Read in arguments from command line
!----------------------------------------------------------------------

      iargs = command_argument_count()
      if (iargs.lt.2) then
        write (*,*) 'usage:  ctfdiff.exe [file1] [file2]'
        nfail=nfail+1
        goto 900
      endif

      call get_command_argument(1,fname1)
      call get_command_argument(2,fname2)

      write (*,'(/,1x,2a)') 'reading h5 file: ', trim(fname1)
      inquire(file=fname1, exist=ifxst)
      if (.not.ifxst) then
        write (*,*) 'ERROR: input file ',trim(fname1),' does not exist'
        nfail=nfail+1
        goto 900
      endif

      write (*,'(1x,2a)') 'reading h5 file: ', trim(fname2)
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

!--- loop over all statepoints and do comparisons

      group_name='STATE_0000'
      nstate=0

      do
        nstate=nstate+1
        write (group_name(7:10),'(i4.4)') nstate
        call h5lexists_f(file_id1, group_name, ifxst, ierror)
        if (.not.ifxst) exit

        call readstate(file_id1, file_id2, nstate, nfail)

      enddo

!--------------------------------------------------------------------------------
! Close File
!--------------------------------------------------------------------------------
      call h5fclose_f(file_id1, ierror)
      call h5fclose_f(file_id2, ierror)

!--------------------------------------------------------------------------------
! Print Results
!--------------------------------------------------------------------------------

! --- print summary table of all statepoints here?  max temp?

  900 continue

      if (nfail.gt.0) then
        write (*,'(/,a)') 'Overall FAIL'
        call exit(nfail)    ! return error code
      else
        write (*,'(/,a)') 'Overall PASS'
      endif

      end program

!=======================================================================
!
!  Subroutine to read a single statepoint from HDF file
!
!=======================================================================
      subroutine readstate(file_id1, file_id2, nstate, nfail)
      use hdf5
      use mod_hdftools, only : hdf5_read_double
      implicit none

      integer(hid_t), intent(in) :: file_id1, file_id2
      integer,        intent(in) :: nstate
      integer                    :: nfail

!--- local variables

      integer            :: ierror
      integer            :: n

      logical            :: ifmissing
      logical            :: ifxst

      real(8)            :: qtmax1, qtmax2
      real(8)            :: qtmaxdiff
      real(8)            :: qtmaxtol=1.0d0   ! tolerance [C]

      real(8)            :: xmax           ! max pin difference (%)
      real(8)            :: pintol=0.5d0   ! pin power tolerance (%)

!**** Bob - the tolerance for each distribution is "pintol"
!**** This may have to be broken up and assign a unique tolerance for each distribution

      character(len=100) :: dataset
      character(len=12)  :: statename

      integer, parameter :: maxdist=7        ! number of distributions to check
      character(len=40)  :: cdist(maxdist)    ! names of distributions

!--- initialize

  ! define list of distributions to check here

      cdist(1)="channel_liquid_temps [C]"
      cdist(2)="pin_fueltemps [C]"
      cdist(3)="pin_powers [W per cm]"
      cdist(4)="Rod_Surface_Temp_SE_Quad [C]"
      cdist(5)="Rod_Surface_Temp_SW_Quad [C]"
      cdist(6)="Rod_Surface_Temp_NW_Quad [C]"
      cdist(7)="Rod_Surface_Temp_NE_Quad [C]"

      ierror=0
      ifmissing=.false.

      write (*,*)

      statename='STATE_0000/'
      write (statename(7:10),'(i4.4)') nstate

!-----------------------
!  check scalar values
!-----------------------

      qtmax1=0.0d0
      qtmax2=0.0d0

      dataset=trim(statename)//'Quantities of Interest/Clad Max Temp/Temperature [C]'

      call h5lexists_f(file_id1, dataset, ifxst, ierror)
      if (ifxst) then
        call hdf5_read_double(file_id1, dataset, qtmax1)
      else
        nfail=nfail+1
        ifmissing=.true.
        write (*,*) 'FAIL - qtmax dataset does not exist on file 1'
      endif

      call h5lexists_f(file_id2, dataset, ifxst, ierror)
      if (ifxst) then
        call hdf5_read_double(file_id2, dataset, qtmax2)
      else
        nfail=nfail+1
        ifmissing=.true.
        write (*,*) 'FAIL - qtmax dataset does not exist on file 2'
      endif

      if (.not. ifmissing) then

        qtmaxdiff=qtmax2-qtmax1

        write (*,'(/,1x,2a)') trim(dataset), ' comparisons'
        write (*,'(2x,a, f12.7)')   'qtmax1  =', qtmax1
        write (*,'(2x,a, f12.7)')   'qtmax2  =', qtmax2
        write (*,'(2x,a, f12.2,a)') 'diff   =', qtmaxdiff,' [C]'
        write (*,'(2x,a, f12.2,a)') 'tol    =', qtmaxtol ,' [C]'
  
        if (abs(qtmaxdiff).lt.qtmaxtol) then
          write (*,*) 'PASS - difference is less than tolerance'
        else
          nfail=nfail+1
          write (*,*) 'FAIL - difference exceeds tolerance'
        endif
      endif

!-----------------------
!  check distributions
!-----------------------

      do n=1, maxdist

        dataset=trim(statename)//trim(cdist(n))

        call h5lexists_f(file_id1, dataset, ifxst, ierror)
        if (.not.ifxst) then
          nfail=nfail+1
          ifmissing=.true.
          write (*,*) 'FAIL - dataset does not exist on file 1'
        endif

        call h5lexists_f(file_id2, dataset, ifxst, ierror)
        if (.not.ifxst) then
          nfail=nfail+1
          ifmissing=.true.
          write (*,*) 'FAIL - dataset does not exist on file 2'
        endif

        if (.not.ifmissing) then
          call pin_compare(file_id1, file_id2, dataset, xmax)
          write (*,320) pintol
          if (abs(xmax).lt.pintol) then
            write (*,*) 'PASS - pin power difference is less than tolerance'
          else
            nfail=nfail+1
            write (*,*) 'FAIL - pin power difference exceeds tolerance'
          endif
        endif
      enddo
  320 format (3x,'tolerance = ', f5.2,' %')

!--- return

      return

      end subroutine readstate
!=======================================================================
!
!  Subroutine to read two pin_power datasets and calculate RMS
!
!=======================================================================
      subroutine pin_compare(file_id1, file_id2, dataset, xmax)
      use hdf5
      use mod_hdftools, only : h5info, hdf5_read_double
      implicit none
      integer(hid_t),   intent(in)  :: file_id1, file_id2
      character(len=*), intent(in)  :: dataset
      real(8),          intent(out) :: xmax   ! return max difference (%)

      integer :: ip, jp, k, na, np
      integer :: nassm, kd, npin
      integer :: ndim         ! number of array dimensions
      integer :: idim(10)     ! array dimension sizes
      integer :: itype        !
      integer :: kmax(4)      ! location of max difference
      integer :: lmax(4)      ! location of max power

      logical :: ifbad        ! flag for bad data

      real(8)              :: p1, dd, dmax
      real(8)              :: pmax1, pave1
      real(8)              :: rms
      real(8), allocatable :: power1(:,:,:,:)
      real(8), allocatable :: power2(:,:,:,:)

!  find dimensions so we can allocate

      xmax=999999.0d0   ! set high in case reads fail
      ifbad=.false.

      call h5info(file_id1, dataset, itype, ndim, idim)

      nassm=idim(1)    ! order (nassm, kd, npin, npin)
      kd   =idim(2)
      npin =idim(4)

!d    write (*,*) 'debug pin: ndim  = ', ndim
!d    write (*,*) 'debug pin: nassm = ', nassm
!d    write (*,*) 'debug pin: kd    = ', kd
!d    write (*,*) 'debug pin: npin  = ', npin

      if (ndim .ne.4) then
        ifbad=.true.
        write (*,*) 'invalid dimensions in pin data'
      endif
      if (nassm.eq.0) then
        ifbad=.true.
        write (*,*) 'invalid number of assemblies in pin data'
      endif
      if (npin .eq.0) then
        ifbad=.true.
        write (*,*) 'invalid number of pins in pin data'
      endif
      if (idim(3).ne.idim(4)) then
        ifbad=.true.
        write (*,*) 'invalid npin in pin data'
      endif
      if (ifbad) return   ! return with big xmax

      allocate (power1(nassm, kd, npin, npin))
      allocate (power2(nassm, kd, npin, npin))

      call hdf5_read_double(file_id1, dataset, idim(1), idim(2), idim(3), idim(4), power1)
      call hdf5_read_double(file_id2, dataset, idim(1), idim(2), idim(3), idim(4), power2)

      rms=0.0d0
      dmax=0.0d0
      np=0
      kmax(:)=0     ! location of max difference
      lmax(:)=0     ! location of max power
      pmax1=0.0d0   ! max power of distribution 1
      pave1=0.0d0   ! ave power of distribution 1
      do ip=1, npin
        do jp=1, npin
          do k=1, kd
            do na=1, nassm
              p1=power1(na,k,jp,ip)
              if (p1.gt.0.0d0) then
                np=np+1
                pave1=pave1+p1
                if (p1.gt.pmax1) then
                  pmax1=p1
                  lmax(1)=ip
                  lmax(2)=jp
                  lmax(3)=k
                  lmax(4)=na
                endif
                dd=abs(power2(na,k,jp,ip)-p1)
                rms=rms+dd*dd
                if (dd.gt.dmax) then
                  dmax=dd
                  kmax(1)=ip
                  kmax(2)=jp
                  kmax(3)=k
                  kmax(4)=na
                endif
              endif
            enddo
          enddo
        enddo
      enddo

      if (np.gt.0) then
        rms=sqrt(rms/dble(np))
        pave1=pave1/dble(np)
      endif

      xmax=dmax*100.0d0
 
      deallocate (power2)
      deallocate (power1)

      write (*,'(/1x,a)') 'Distribution comparisons (averages do not include volume weight)'
      write (*,120) np
      write (*,126) pmax1, lmax(:)
      write (*,125) pave1
      write (*,131) dmax*100.0d0, kmax(:)
      write (*,130) rms*100.0d0
 120  format (3x,'num values',5x,i10)
 125  format (3x,'ave power1     ', f10.4)
 126  format (3x,'max power1     ', f10.4,'   at (ip,jp,k,na) ', 4i4)
 130  format (3x,'rms difference ', f10.4,' %')
 131  format (3x,'max difference ', f10.4,' % at (ip,jp,k,na) ', 4i4)

      return
      end subroutine pin_compare
!=======================================================================
