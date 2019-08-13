%  Template for CASL reports
%  by Seth R. Johnson and Tara M. Pandya
% licensed under Creative Commons (attribution): http://creativecommons.org/licenses/by/3.0/us/
%
% Usage: \documentclass{caslreport}
% define \title and \author as usual, and also define \classname and \reportnum

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{caslreport}
[2016/09/15 v1.00 CASL Report template class, Tara M. Pandya]

%%% OPTIONS %%%
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{srjcommon}}
\ProcessOptions

%%% REQUIRED CLASSES %%%
%\RequirePackage{fix2col}
% scott changed from 12pt to 11pt
\LoadClass[letterpaper,titlepage,twoside,11pt]{srjcommon}
\geometry{letterpaper,left=1in,right=1in,top=1.0in,bottom=1.0in,%
          headheight=34pt}
\RequirePackage{pdfpages}
%\geometry{letterpaper,height=8in,width=6in}

%% Turn on Times-New-Roman
%x \RequirePackage{newtxtext}
%x \RequirePackage{newtxmath}

\newif\if@reportnumdefined
\@reportnumdefinedfalse
\def\@reportnum{\PackageWarning{caslreport}{No report number has been defined.}}
\newcommand{\reportnum}[1]{\def\@reportnum{#1}\@reportnumdefinedtrue}

%%% CLASS NAME AND TITLES %%%
\AtBeginDocument{%
 \hypersetup{pdfauthor={\@author}, pdftitle={\@title}, pdfsubject={\@classname}}
 \pagenumbering{roman}

 % need to use if \maketitle is used (which destroys \@title)
 \let\@preservedTitle=\@title
 \let\@preservedDate=\@date
 \let\@preservedAuthor=\@author

 \newcommand{\fhFormat}{\small}

 \usepackage{color}
 \definecolor{blue}{rgb}{0.0,0.502,1.0}
 \definecolor{black}{rgb}{0,0,0}
 % global page style
 \pagestyle{fancy}
 \fancyhead{} % clear all header fields
 \fancyhead[LE, RO]{\fhFormat \color{blue}\@preservedTitle} %
 \fancyhead[LO, RE]{\includegraphics[width=0.25\textwidth]{casl/CASL.png}} %
 \fancyfoot{} % clear all footer fields
 \fancyfoot[C]{\fhFormat \thepage} %
 \fancyfoot[LE, RO]{\fhFormat \textcolor{blue}{C}onsortium %
   for \textcolor{blue}{A}dvanced \textcolor{blue}{S}imulation %
   of \textcolor{blue}{L}WRs}
 \if@reportnumdefined
 \fancyfoot[LO, RE]{\fhFormat \@reportnum}
 \fi %
 \renewcommand{\footrulewidth}{0.0pt}%
 \renewcommand{\headrulewidth}{0.0pt}%

 % table of contents style
 \fancypagestyle{plain}{%
   \fancyhead{} % clear all header fields
   \fancyhead[LE, RO]{\fhFormat \color{blue} \@preservedTitle} %
   \fancyhead[LO, RE]{\includegraphics[width=0.25\textwidth]{casl/CASL.png}} %
   \fancyfoot{} % clear all footer fields
   \fancyfoot[C]{\fhFormat \thepage}%
   \fancyfoot[LE, RO]{\fhFormat \textcolor{blue}{C}onsortium %
     for \textcolor{blue}{A}dvanced \textcolor{blue}{S}imulation %
     of \textcolor{blue}{L}WRs}
   \if@reportnumdefined
   \fancyfoot[LO, RE]{\fhFormat \@reportnum}
   \fi %
   \renewcommand{\headrulewidth}{0.0pt}%
   \renewcommand{\footrulewidth}{0.0pt}%
 }

% first page style
 \fancypagestyle{abstract}{%
   \pagestyle{fancy}
   \fancyhead{} % clear all header fields
   \fancyfoot{} % clear all footer fields
   \fancyfoot[LE, RO]{\fhFormat \color{blue} \@preservedTitle} %
   \fancyhead[LO, RE]{\includegraphics[width=0.25\textwidth]{casl/CASL.png}} %
   \fancyfoot[C]{\fhFormat \thepage}%
   \fancyfoot[LE, RO]{\fhFormat \textcolor{blue}{C}onsortium %
     for \textcolor{blue}{A}dvanced \textcolor{blue}{S}imulation %
     of \textcolor{blue}{L}WRs}
   \if@reportnumdefined
   \fancyfoot[LO, RE]{\fhFormat \@reportnum}
   \fi %
   \renewcommand{\footrulewidth}{0pt}
   \renewcommand{\headrulewidth}{0pt}%
 }

 % make the cover pages   - update to include page 4 for signatures
 \thispagestyle{empty}
 \includepdf[pages=1-4, pagecommand={\thispagestyle{empty}}]{casl/cover.pdf}
 \def\and{and }

}

%%%%%%  VISUAL STUFF %%%%%%

% Include some packages with specific formats
\usepackage[font=bf, labelsep=period]{caption}
\usepackage[font=bf]{subcaption}
\usepackage{tocloft}

%\usepackage{etoolbox}
%\makeatletter
%\patchcmd{\l@section}{#1}{\texorpdfstring{\MakeUppercase{#1}}}{}{}% Sections use UPPERCASE in ToC
%\patchcmd{\l@subsection}{#1}{\texorpdfstring{\MakeUppercase{#1}}}{}{}% Subsections use UPPERCASE in ToC
%\makeatother

% Format toc, lof, lot titles
\renewcommand{\contentsname}{\centerline{\bfseries\large CONTENTS}}
\renewcommand{\listtablename}{\centerline{\bfseries\large TABLES}}
\renewcommand{\listfigurename}{\centerline{\bfseries\large FIGURES}}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}

% use Times font
%\RequirePackage[T1]{fontenc}
%\RequirePackage{mathptmx}

%use Utopia Regular with Fourier
%\usepackage{fourier}
% revert calligraphy math:
\SetMathAlphabet{\mathcal}{normal}{OMS}{xmdcmsy}{m}{n}%
\usepackage{microtype}

%use nicer tables
\usepackage{booktabs}

%set up color links (MUST be done in the preamble)
\hypersetup{colorlinks=true,
            citecolor=[rgb]{0.0,0.0,0.0},
            linkcolor=[rgb]{0.0,0.0,0.0},
            }

\newcommand{\frontmatter}{}
\newcommand{\mainmatter}{\pagenumbering{arabic}}

% allow more floats
\renewcommand{\bottomfraction}{0.5}
%\renewcommand\floatpagefraction{.9}
%\renewcommand\topfraction{.9}
%\renewcommand\bottomfraction{.9}
%\renewcommand\textfraction{.1}
%\setlength{\parindent}{0pt}
%\setlength{\parskip}{12pt plus 4pt minus 2pt}

%don't show sub-sub-sections in TOC
\setcounter{tocdepth}{2}

%%redefine sections (need texorpdfstring when using hyperref)
\usepackage[bf,medium,raggedright]{titlesec}
\titleformat{\section}{\bf\large}{\thetitle.}{1ex}{\MakeUppercase}[]
\titleformat{\subsection}{\bf}{\thetitle.}{1ex}{\MakeUppercase}[]
\titleformat*{\subsubsection}{\bf\itshape}
