   program expandxml
   implicit none
!=======================================================================
!
!  Program to read and update and XML file for thermal expansion
!
!  Copyright (c) 2016 Core Physics, Inc.
!
!  Distributed under the MIT license.
!  See the LICENSE file in the main directory for details.
!
!  Reference:
!
!      Scott Palmtag, Core Physics Inc.
!      "Investigation of Thermal Expansion Effects in MPACT"
!      CASL Report CASL-U-2016-1015-000
!      February 23, 2016
!
!=======================================================================
!
!  2016-03-01 - code for Milestone
!  2016-04-07 - update to expand everything except fuel at moderator temperature
!
!  Usage:
!   expandxml.exe {-replace} {-tf910.0} {-tm560.0} {-3d} [file(s).xml]
!     -replace will replace the xml file, otherwise a copy is made
!     -3d      will perform axial expansion (recommended)
!     -tfxxx   overwrite fuel temperature (K)
!     -tmxxx   overwrite moderator temperature (K)
!
!  Assumptions: 
!  1. Fuel is at "tfuel", all other materials are at average mod temperature
!      (ignore increased temperature of clad)
!  2. In the radial direction, all non-fuel material densities are expanded like clad,
!       and at the average mod temp
!  3. In the axial direction, all material densities are expanded like fuel
!  4. The assembly pitch and plate dimensions are expanded as SS, but the SS densities
!       are corrected like other materials (slight inconsistency)
!
!  3D expansion assumptions:
!   * upper and lower core plates expanded by steel factor
!   * total height                    by fuel factor
!   * assembly axial                  by fuel factor
!   * assembly grid heights           by fuel factor
!   * assembly grid locations         by fuel factor
!   * assembly upper and lower nozzle by fuel factor (to match total height)
!   * edit bounds                     by fuel factor (to match total height)
!   * Density decreased by 3D fuel factors
!   * All guide tube materials (detectors, waba, pyrex, etc.) are expanded as cladding
!
!  @version CVS $Id: expandxml.f90,v 1.20 2016/05/26 02:28:03 scott Exp $
!
!=======================================================================

      integer, parameter :: maxlen=1000    ! max line length in xml file
      integer, parameter :: maxline=2000   ! increase for P7

      character(len=maxlen) :: line(maxline)
      character(len=200)    :: fname

      integer :: numfile
      integer :: nline
      integer :: ia
      integer :: kk, k1, k2
      integer :: n
      integer :: mlen                ! maximum character length in xml file
      integer :: npins               ! number of pins across an assembly

      integer :: ldenfuel            ! line number of fuel density
      integer :: ldenclad            ! line number of clad density
      integer :: ltfuel
      integer :: lppitch
      integer :: lapitch
      integer :: lfuelcell

      real(8) :: tfuel               ! fuel temperature
      real(8) :: tinlet              ! tinlet
      real(8) :: tmod                ! mod  temperature
      real(8) :: tfuelin             ! fuel temperature from argument list
      real(8) :: tmodin              ! mod  temperature from argument list

      real(8) :: ftef                ! fuel thermal expansion factor
      real(8) :: ctef                ! clad thermal expansion factor
      real(8) :: pptef               ! ppitch thermal expansion factor
      real(8) :: aptef               ! apitch thermal expansion factor

      real(8) :: dfact

      logical :: ifreplace=.false.   ! replace XML file
      logical :: if3d     =.false.   ! 3D expansion

      real(8), external :: te_martin
      real(8), external :: te_zirc_diam
      real(8), external :: te_ss304

!--- read command line and loop over arguments

      write (*,*) 'Thermally expanding dimensions on XML file'

      tfuelin=-100.0d0    ! set negative if not used
      tmodin =-100.0d0    ! set negative if not used

      mlen=0

      ia=iargc()
      do numfile=1, ia
        call getarg(numfile,fname)

        if (fname.eq.'-replace') then    ! replace/overwrite xml file
          ifreplace=.true.
          cycle
        endif
        if (fname.eq.'-3d') then         ! perform 3D expansion
          if3d=.true.
          cycle
        endif
        if (fname(1:3).eq.'-tf') then    ! read fuel temperature
          read (fname(4:),*) tfuelin
          cycle
        endif
        if (fname(1:3).eq.'-tm') then    ! read mod temperature
          read (fname(4:),*) tmodin
          cycle
        endif
        if (fname(1:1).eq.'-') then
          write (*,'(2a)') 'unknown command line option: ', trim(fname)
          stop 'invalid command line option'
        endif

        write (*,'(2a)') ' processing file ', trim(fname)

!--- read file and store in buffer

        open (12,file=fname,status='old')

        nline=0
        do
          read (12,'(a)',end=100) line(nline+1)
          nline=nline+1
          if (nline.ge.maxline) stop 'max line number exceeded'
          mlen=max(mlen,len_trim(line(nline)))
        enddo
   100  continue

        write (*,*) 'number of lines     in xml = ', nline
        write (*,*) 'maximum line length in xml = ', mlen
        if (mlen.gt.maxlen-10) write (0,*) '*** possible line truncation'

        if (ifreplace) then
          close (12,status='delete')
        else
          close (12)
          fname=trim(fname)//'2'   ! create new file
        endif

!--- read temperatures

        tfuel=0.0d0
        tmod =583.0d0   ! use value from P6 CTF calculation
        tinlet=565.0d0  ! use value from P6 CTF calculation

        ltfuel=0
        npins=0

        do n=1, nline

          kk=index(line(n),'"tfuel"')
          if (kk.gt.0) then
            if (ltfuel.gt.0) stop 'multiple fuel temperatures found'
            ltfuel=n
            call read_value(line(n), 'tfuel', k1, k2)
            read (line(n)(k1:k2),*) tfuel      ! read tfuel value
!d          write (*,*) 'tfuel=', tfuel
          endif

          kk=index(line(n),'"tinlet"')
          if (kk.gt.0) then
            call read_value(line(n), 'tinlet', k1, k2)
            read (line(n)(k1:k2),*) tinlet
            tinlet=tinlet+273.15d0
!d          write (*,*) 'tinlet =', tinlet
          endif

          kk=index(line(n),'"thexp_mod"')         ! optional input
          if (kk.gt.0) then
            call read_value(line(n), 'thexp_mod', k1, k2)
            read (line(n)(k1:k2),*) tmod          ! read moderator value
!d          write (*,*) 'tmod =', tmod
          endif

          kk=index(line(n),'"num_pins"')   ! read number of pins
          if (kk.gt.0) then
            call read_value(line(n), 'num_pins', k1, k2)
            read (line(n)(k1:k2),*) npins
!d          write (*,*) 'found npins = ', npins
          endif

        enddo

        if (abs(tinlet-tfuel).lt.1.0d0) then
          tmod=tfuel
          write (*,*) 'detected HZP case - setting tmod to tfuel'
        endif

        if (ltfuel.eq.0) stop 'fuel temperature not found in xml file'
        if (npins .eq.0) stop 'num_pins not found in xml file'

        if (tfuelin.gt.0.0d0) tfuel=tfuelin    ! use command line value overwrite
        if (tmodin .gt.0.0d0) tmod =tmodin     ! use command line value overwrite

        if (tfuel.le.299.0d0) then
          write (*,*) 'skipping thermal expansion for cold case'
          goto 999    ! skip expansion if cold case
        endif

!--- calculate expansion factors

  ! **** read factors from input??? 

        ftef=te_martin(tfuel)        ! fuel   TE factor
        ctef=te_zirc_diam(tmod)      ! clad   TE factor
        pptef=ctef                   ! ppitch TE factor
        aptef=te_ss304(tmod)         ! apitch TE factor

        if (npins.eq.1) pptef=aptef   ! for single pin, set ppitch=apitch

        write (*,*)
        write (*,*) 'Expansion factors:'
        write (*,210) 'fuel   ', tfuel, ftef
        write (*,210) 'clad   ', tmod , ctef
        write (*,210) 'ppitch ', tmod , pptef
        write (*,210) 'apitch ', tmod , aptef

!--- update pin and assembly pitch

        lppitch=0   ! check to make sure we encounter at least one ppitch
        lapitch=0

        do n=1, nline

          kk=index(line(n),'"ppitch"')    ! may be multiple occurances
          if (kk.gt.0) then
            lppitch=n
            call update_scalar(line(lppitch), 'ppitch', pptef)
          endif

          kk=index(line(n),'"apitch"')    ! may be multiple occurances
          if (kk.gt.0) then
            lapitch=n
            call update_scalar(line(lapitch), 'apitch', aptef)
          endif

        enddo

        if (lppitch .eq.0) stop 'pin pitch not found'
        if (lapitch .eq.0) stop 'assm pitch not found'

!--- read cells and update pin dimensions

        lfuelcell=0

        do n=1, nline
          kk=index(line(n),'"Cell_')      ! *** read any cell name
          if (kk.gt.0) then

            write (*,*)
            write (*,*) 'Cell ', trim(line(n)(kk:))

            call read_value(line(n+5), 'type', k1, k2)    ! guide tube or fuel cell?

            if (line(n+5)(k1:k2).eq.'fuel') then   ! fuel rod
              write (*,*) 'Fuel cell'
              lfuelcell=n
              call update_radii(line(n+4), ftef, ctef)
            else     ! other
              write (*,*) 'Non-fuel cell'
              call update_list(line(n+4), 'radii', ctef)
            endif

          endif   ! kk
        enddo

        if (lfuelcell.eq.0) stop 'fuel cell not found'

!--- 3D expansions

        if (if3d) then
          do n=1, nline

            kk=index(line(n),'"lower_thick"')
            if (kk.gt.0) then
              call update_scalar(line(n), 'lower_thick', aptef)
            endif

            kk=index(line(n),'"upper_thick"')
            if (kk.gt.0) then
              call update_scalar(line(n), 'upper_thick', aptef)
            endif

            kk=index(line(n),'"lower_nozzle_height"')
            if (kk.gt.0) then
              call update_scalar(line(n), 'lower_nozzle_height', ftef)
            endif

            kk=index(line(n),'"upper_nozzle_height"')
            if (kk.gt.0) then
              call update_scalar(line(n), 'upper_nozzle_height', ftef)
            endif

            kk=index(line(n),'"height"')   ! both core height and grid height
            if (kk.gt.0) then
              call update_scalar(line(n), 'height', ftef)
            endif

            kk=index(line(n),'"axial_edit_bounds"')
            if (kk.gt.0) then
              call update_list(line(n), 'axial_edit_bounds', ftef)
            endif

            kk=index(line(n),'"axial_elevations"')   ! assembly elevations
            if (kk.gt.0) then
              call update_list(line(n), 'axial_elevations', ftef)
            endif

            kk=index(line(n),'"grid_elev"')    ! assembly grid elevations
            if (kk.gt.0) then
              call update_list(line(n), 'grid_elev', ftef)
            endif

          enddo
        endif       ! if3d

!--- update densities

        ldenfuel=0      ! line number of fuel density
        ldenclad=0      ! line number of fuel density

!  Fuel

        do n=1, nline
          kk=index(line(n),'"Fuel_')    ! may be multiple fuel types
          if (kk.gt.0) then
!d          write (*,*) 'found Fuel ', trim(line(n)(kk:))
            ldenfuel=n+1
            dfact=1.0d0/(ftef*ftef)     ! modify density
            if (if3d) dfact=dfact/ftef
            call update_scalar(line(ldenfuel), 'density', dfact)
          endif
        enddo

!  Update all other materials expand as clad material

        do n=1, nline
          kk=index(line(n),'"Material_')
          if (kk.gt.0) then
!d          write (*,'(1x,3a)') 'adjusting density ', trim(line(n)(kk:)),' as clad material'
            ldenclad=n+1
            dfact=1.0d0/(ctef*ctef)     ! modify density
            if (if3d) dfact=dfact/ftef  ! 3D expansion uses fuel factor
            call update_scalar(line(ldenclad), 'density', dfact)
          endif
        enddo

        if (ldenfuel.eq.0) stop 'fuel density not found'
        if (ldenclad.eq.0) stop 'clad density not found'

!--- write file

  999   continue

        open (12,file=fname)
        do n=1, nline
          write (12,'(a)') trim(line(n))
        enddo
        close (12)

      enddo   ! next file

  210 format (4x,a,f10.2,' K  ',f10.6)

      end

!=======================================================================
!
!  Subroutine to update a double value in an XML line
!  Multiplies value on line by "dfact"
!
!=======================================================================
      subroutine update_scalar(line, target, dfact)
      implicit none
      character(len=*)    :: line
      character(len=*), intent(in) :: target  ! target label  ("density", "ppitch", etc.)
      real(8),          intent(in) :: dfact   ! correction factor

      integer :: k1, k2
      real(8) :: dold            ! old value
      character(len=10) cc

      call read_value(line, target, k1, k2)

      read (line(k1:k2),*) dold       ! read density value
      dold=dold*dfact

      if (dold.lt.0.01d0) then
        write (cc,'(f10.7)') dold    ! gas density
      else
        write (cc,'(f10.5)') dold
      endif
      cc=adjustl(cc)

      line(k1:)=trim(cc)//'"/>         '    ! add trailing blanks

      return
      end subroutine update_scalar

!=======================================================================
!
!  Generic routine to read the "value" from a line of XML
!  e.g. <Parameter name="fuel_names" type="Array(string)" value="{u-235,u-234}"/>
!
!  The subroutines returns the position of the value in the string.
!  The value will be in location line(k1:k2)
!
!=======================================================================
      subroutine read_value(line, target, k1, k2)
      implicit none
      character(len=*), intent(in)  :: line
      character(len=*), intent(in)  :: target   ! name
      integer, intent(out) :: k1, k2            ! output value is in line(k1:k2)

      integer :: kk
      character(len=20) :: tar2   ! target with quotes

      k1=0
      k2=0

      tar2='"'//trim(target)//'"'
      kk=index(line,trim(tar2))   ! confirm target is correct
      if (kk.eq.0) then
        write (*,'(2a)') 'target: ',trim(tar2)
        write (*,'(2a)') 'line:   ',trim(line)
        stop 'error finding target in line'
      endif

      kk=index(line,'value="')
      if (kk.eq.0) stop 'error finding closing quote'
      k1=kk+7
      kk=index(line(k1:),'"')
      k2=k1+kk-2
!de   write (*,'(3a)') '  >',line(k1-1:k2+1),'<'

      return
      end subroutine read_value

!=======================================================================
!
!  Update radii of fuel rod
!
!  Look for annular fuel and ifba
!
!=======================================================================
      subroutine update_radii(line, ftef, ctef)
      implicit none
      character(len=*)    :: line
      real(8), intent(in) :: ftef    ! fuel expansion factor
      real(8), intent(in) :: ctef    ! clad expansion factor

      integer :: k1, k2, k
      integer :: nval

      real(8) :: volifba

      real(8), allocatable :: radii(:)
      real(8), allocatable :: thick(:)

      real(8), save :: clad_outer=-1.0d0

      logical :: ifannular, ifba

      character(len=10) :: label

      label='radii'

      call read_value(line, label, k1, k2)

  ! previous call returns something like {0.4096,0.418,0.475}
      write (*,'(3a)') '  >',line(k1-1:k2+1),'<'

      if (line(k1:k1).ne.'{') stop 'missing left bracket'
      if (line(k2:k2).ne.'}') stop 'missing right bracket'
      k1=k1+1   ! remove bracket
      k2=k2-1   ! remove bracket

!--- count commas to find number of values in line

      nval=1      ! number of values = number of commas + 1
      do k=k1, k2
        if (line(k:k).eq.',') nval=nval+1
      enddo
!d    write (*,*) 'number of values = ', nval

!--- read values

      allocate (radii(nval))
      allocate (thick(nval))
      read (line(k1:k2),*) (radii(k),k=1,nval)   ! comma separated values

      if (nval.lt.2) then
        stop 'fuel cells must have at least 2 radii'
      endif

      if (clad_outer.lt.0.0d0) clad_outer=radii(nval)
      if (clad_outer.ne.radii(nval)) then
        write (*,*) '***** WARNING: inconsistent outer radii of fuel cell *****'
      endif

      thick(1)=radii(1)
      do k=2, nval
        thick(k)=radii(k)-radii(k-1)
      enddo

!--- check for annular fuel or ifba

      ifannular=.false.
      ifba     =.false.

      if (thick(1).lt.0.2d0) then
        ifannular=.true.
        write (*,*) 'found annular fuel cell'
      endif

      if (nval.ge.4 .and. thick(nval-2).lt.0.2) then   ! nval is clad, nval-1 is gap, nval-2 is ifba
        ifba=.true.
        write (*,*) 'found IFBA fuel cell, thickness ', thick(nval-2)
        volifba=(radii(nval-2)**2 - radii(nval-3)**2)*ctef*ctef   ! expanded volume w/o pi
        write (*,*) 'ifba vol1', volifba
      endif

!--- update values

!*************** IFBA

      if (ifannular) then     ! annular fuel
        radii(1)=radii(1)*ftef   ! annulus
        radii(2)=radii(2)*ftef   ! fuel
      else
        radii(1)=radii(1)*ftef   ! fuel
        radii(2)=radii(2)*ctef
      endif

      do k=3, nval
        radii(k)=radii(k)*ctef
      enddo

!--- fix ifba radii to preserve total mass
!  ifba is not a "free surface" because it travels with the fuel diameter
!  therefore, the radii must be adjusted to preserve expanded volume

      if (ifba) then
        radii(nval-2)=sqrt(volifba + radii(nval-3)**2)
        write (*,*) 'ifba vol2', (radii(nval-2)**2 - radii(nval-3)**2)
      endif


!--- write values back to line

      do k=1, nval
        if     (radii(k).lt.10.0d0) then
          write (line(k1:),'(f7.5,",")') radii(k)
          k1=k1+8
        elseif (radii(k).lt.100.0d0) then
          write (line(k1:),'(f8.5,",")') radii(k)
          k1=k1+9
        elseif (radii(k).lt.1000.0d0) then
          write (line(k1:),'(f9.5,",")') radii(k)
          k1=k1+10
        else
          write (line(k1:),'(f10.5,",")') radii(k)
          k1=k1+11
        endif
      enddo
      k1=k1-1   ! remove last comma

      line(k1:)='}"/>'    ! new line will be longer than old line

      deallocate (radii)
      return
      end subroutine update_radii


!=======================================================================
!
!  Update list of doubles
!  Could be grid elevations, edit elevations, pin radii, etc.
!
!=======================================================================
      subroutine update_list(line, label, fact)
      implicit none
      character(len=*)    :: line
      character(len=*), intent(in) :: label
      real(8),          intent(in) :: fact    ! expansion factor

      integer :: k1, k2, k
      integer :: nval
      real(8), allocatable :: radii(:)

      call read_value(line, label, k1, k2)

  ! returns something like {0.4096,0.418,0.475}
      write (*,'(3a)') '  >',line(k1-1:k2+1),'<'

      if (line(k1:k1).ne.'{') stop 'missing left bracket'
      if (line(k2:k2).ne.'}') stop 'missing right bracket'
      k1=k1+1   ! remove bracket
      k2=k2-1   ! remove bracket

!--- count commas

      nval=1      ! number of values = number of commas + 1
      do k=k1, k2
        if (line(k:k).eq.',') nval=nval+1
      enddo
!d    write (*,*) 'number of values = ', nval

!--- read values

      allocate (radii(nval))
      read (line(k1:k2),*) (radii(k),k=1,nval)   ! comma separated values

      do k=1, nval
         radii(k)=radii(k)*fact
      enddo

!--- write values back to line

      do k=1, nval
        if     (radii(k).lt.10.0d0) then
          write (line(k1:),'(f7.5,",")') radii(k)
          k1=k1+8
        elseif (radii(k).lt.100.0d0) then
          write (line(k1:),'(f8.5,",")') radii(k)
          k1=k1+9
        elseif (radii(k).lt.1000.0d0) then
          write (line(k1:),'(f9.5,",")') radii(k)
          k1=k1+10
        else
          write (line(k1:),'(f10.5,",")') radii(k)
          k1=k1+11
        endif
      enddo
      k1=k1-1   ! remove last comma

      line(k1:)='}"/>'    ! new line will be longer than old line

      deallocate (radii)
      return
      end subroutine update_list

!=======================================================================
!  Thermal expansion coefficient of UO2 from Martin 1988
!  (Also in Fink 2000)
!
! Martin, D. G., 
! “The Thermal Expansion of Solid UO2 and (U, Pu) Mixed Oxides: A Review and Recommendations.”,
! J Nucl Mater,  152, 94–101 (1988).
!
! The original correlation assumed a base temperature of 273K
! This subroutine adds an additional factor to make the base temp 293K
!=======================================================================

      function te_martin(t)
      implicit none
      real(8) :: te_martin
      real(8), intent(in) :: t  ! fuel temperature (K)

!  assumes that non-reversible (sintering) or expansion ("solarization") of samples has not occurred

      if (t.lt.273d0) then
        stop 'temperature less than lower bound of correlation'
      elseif (t.lt.923.0d0) then
        te_martin=0.99734d0 + 9.802d-6*T - 2.705d-10*T*T + 4.391d-13*T*T*T    ! 273K to 923K
      elseif (t.le.3120.0d0) then
        te_martin=0.99672d0 + 1.179d-5*T - 2.429d-9*T*T  + 1.219d-12*T*T*T     ! 923K to 3120K
      else
        stop 'temperature exceeds upper bound of correlation'
      endif

      te_martin=te_martin*0.999800d0    ! correct from 273 to 293K

      return
      end function te_martin

!=======================================================================
!  Thermal expansion coefficient of Zircaloy cladding - diameter expansion
!  From Eq.(4) of IAEA_TE_1496 page 273 - diameter expansion
!
!  Zirconium is not isotropic, so need a different formula for axial expansion
!
!  The original formulation had a base temp of 300K
!  This function adjusts the formula to use a base of 293K
!
!=======================================================================
      function te_zirc_diam(t)
      implicit none
      real(8) :: te_zirc_diam
      real(8), intent(in) :: t  ! zirc temperature (K)

!x    te_zirc_diam=-2.128d-3 + 7.092d-6*t
      te_zirc_diam= 1.0d0 + 7.092d-6*(t-293.0d0)     ! adjust to 293 and add one

      return
      end function te_zirc_diam

!=======================================================================
!  Thermal expansion coefficient of SS304
!
!  From:
!  "Thermal Linear Expansion of Nine Selected AISI Stainless Steels",
!  CINDAS Report 51, April (1978).  
!  http://www.dtic.mil/dtic/tr/fulltext/u2/a129159.pdf
!
!  Report has additional values below 293 and above 1000K
!
!=======================================================================
      function te_ss304(t)
      implicit none
      real(8) :: te_ss304
      real(8), intent(in) :: t  ! input temperature (K)

      integer :: ii, j
      real(8) :: x, ffnew

      integer, parameter :: ntab=10

      real(8) :: tk(ntab)   ! temperatures (K)
      real(8) :: ff(ntab)   ! coefficients (%)

      data tk / 293.0d0, 300.0d0, 350.0d0, 400.0d0, 500.0d0, &
                600.0d0, 700.0d0, 800.0d0, 900.0d0, 1000.0d0 /
      data ff / 0.0d0, 0.01d0, 0.086d0, 0.167d0, 0.338d0, &
                0.519d0, 0.709d0, 0.907d0, 1.112d0, 1.323d0 /

      if (t.lt.tk(1))    stop 'invalid temperature in te_ss304'
      if (t.gt.tk(ntab)) stop 'invalid temperature in te_ss304'

      ii=1     ! lower value in table
      do j=1, ntab-1
        if (t.gt.tk(j)) ii=j
      enddo 
!dbg  write (0,*) 'temp ', t
!dbg  write (0,*) 'table bounds' , ii, tk(ii), tk(ii+1)

      x=(t-tk(ii))/(tk(ii+1)-tk(ii))
!dbg  write (0,*) 'chi ', t, x

      ffnew=ff(ii)+x*(ff(ii+1)-ff(ii))   ! factor in percent

      te_ss304= 1.0d0+ffnew*0.01d0   ! convert to multiplier

      return
      end function te_ss304

