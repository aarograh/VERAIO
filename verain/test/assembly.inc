[ASSEMBLY]
  title "Westinghouse 17x17"
  npin 17 
  ppitch 1.260
  
  uo2 U31 10.257 / 3.1

  cell 1     0.4096 0.418 0.475 / U31 he zirc
  cell 100          0.561 0.602 / mod    zirc       ! guide tube
  
  lattice FUEL1
     100
       1 1
       1 1 1
     100 1 1 100
       1 1 1   1 1
       1 1 1   1 1 100
     100 1 1 100 1   1 1
       1 1 1   1 1   1 1 1
       1 1 1   1 1   1 1 1 1

  axial A1   11.951 
      FUEL1 377.711

  grid END inc  1017 3.866
  grid MID zirc 875  3.810

  grid_axial
      END  13.884
      MID  75.2
      MID 127.4
      MID 179.6
      MID 231.8
      MID 284.0
      MID 336.2
      END 388.2

  lower_nozzle  ss 6.05  6250.0  ! mat, height, mass (g)
  upper_nozzle  ss 8.827 6250.0  ! mat, height, mass (g)

  lower_nozzle_gap_height  4.231
  lower_pincap_height      1.67

  upper_nozzle_gap_height  2.12
  upper_pincap_height      1.67
  upper_plenum_height      16
  
 !! dancoff                   ! assembly_dancoff_map
 !!   0.000
 !!   0.287 0.315                            
 !!   0.287 0.315 0.315                        
 !!   0.000 0.287 0.286 0.000                        
 !!   0.287 0.316 0.316 0.284 0.299                
 !!   0.288 0.317 0.316 0.287 0.267 0.000
 !!   0.000 0.286 0.286 0.000 0.270 0.286 0.321        
 !!   0.287 0.319 0.319 0.286 0.315 0.335 0.333 0.337    
 !!   0.323 0.322 0.321 0.322 0.320 0.322 0.323 0.322 0.310

