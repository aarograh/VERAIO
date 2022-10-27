%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File  : vera-ornltm.cls
% Author: Tara M Pandya and Seth R Johnson
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{vera-ornltm}[2018/10/13 VERA Technical Memorandum class]

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% OPTIONS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\ProcessOptions\relax
\LoadClass[11pt,letterpaper]{article}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% STYLING
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[usenames]{color} % colored fonts and boxes
\RequirePackage{xcolor}
\RequirePackage{wallpaper} % background on cover page
\RequirePackage{emptypage} % hide footers on blank pages
\RequirePackage[pdfusetitle]{hyperref} % url and links in PDF
\RequirePackage[shortcuts,acronym,nonumberlist,nogroupskip,nopostdot]{glossaries} % acronym support
\RequirePackage{tocloft} % table of contents styling


% Load document style
\RequirePackage{vera-ornltm-style}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% VARIABLES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Make custom blue to match word blue
\definecolor{DocNameBlue}{RGB}{154,189,251}
% CASL blue
\definecolor{caslblue}{HTML}{4F81BD}
\definecolor{caslcolor1}{HTML}{E9EDF4}
\definecolor{caslcolor2}{HTML}{D0D8E8}

% Use the \reportnum command to define a report number.
\newif\if@reportnumdefined
\@reportnumdefinedfalse
\def\@reportnum{ORNL/SPR-XXXX/XXX%
\PackageWarning{vera-ornltm}{No SPR report number has been defined.}}
\newcommand{\reportnum}[1]{\def\@reportnum{#1}\@reportnumdefinedtrue}

\newif\if@reportdraft
\@reportdraftfalse
\newcommand{\reportdraft}{\@reportdrafttrue}

% Use the \restrict command to add qualifications to the document's restriction.
% For example, add ``OUO'' and such.
\newif\if@restrictdefined
\@restrictdefinedfalse
\newcommand{\restrict}[1]{\def\@restrict{#1}\@restrictdefinedtrue}

% Define uppercase names
\newcommand\ornltmabstractname{ABSTRACT}
\newcommand\ornltmlofname{LIST OF FIGURES}
\newcommand\ornltmlotname{LIST OF TABLES}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% COVER
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Bold sans-serif
\newcommand{\textbsf}[1]{{\bfseries\sffamily #1}}
% Bold italics
\newcommand{\textbi}[1]{{\bfseries\itshape #1}}
% ORNL official green color
\definecolor{ornlgreen}{RGB}{0,121,52}
% Green can render as this color (???)
\definecolor{ornldarkgreen}{RGB}{52,118,60} % from included ORNL logo

% Footer for cover page
\fancypagestyle{coverpage}
{
  \renewcommand\headrulewidth{0pt}
  \fancyhf{}
}

\def\makecoverpage{%
\newgeometry{top=0.5in,bottom=0.5in,right=.5in,left=0.5in}

\begin{titlepage}
\thispagestyle{coverpage}
\ThisCenterWallPaper{1.0}{vera-cover-background.png}

%% REPORT NUMBER %%
\begin{minipage}[c][0.5in]{7.5in}%
\raggedleft
\large\textbsf{\textcolor{caslblue}{\@reportnum}}
\end{minipage}%

%% TITLE AND DATE %%
\begin{minipage}[c][3.0in]{0.6\textwidth}%
  \raggedright
  \Huge\textbsf{\textcolor{white}{%
    \@title
  }}
  \vspace{\baselineskip}
  
  \large\textbsf{\textcolor{white}{\@date}}
\end{minipage}%

\vspace*{2\baselineskip}

%%% AUTHOR %%%
\begin{minipage}[c]{2in}%
\def\and{\\}% Newline between authors
\large\sffamily\color{caslblue}{
\setlength\tabcolsep{0pt}
\begin{tabular}[t]{l}
 \@author%
\end{tabular}
}

% \vspace{2\baselineskip}

%%% NOTICES %%%
% If restrict and draft, show restrict + draft
% If restrict and not draft, show restrict
% If not restrict and draft, show draft
% If not restrict and not draft, show ``approved for public release"
% \vspace{\stretch{1}}
\end{minipage}%

\begin{center}
\begin{minipage}[c]{3in}%
\if@reportdraft{%
  \textbsf{\large Draft. Not for public release.}%
}\fi%
%
\if@restrictdefined{%
\par\@restrict%
}\else%
\if@reportdraft\relax\else{%
\textbsf{%
  Approved for public release. \\
  Distribution is unlimited.}%
}\fi%
\fi%
\end{minipage}
\end{center}

\vspace{\stretch{1}}

%% BOTTOM RIGHT NOTICE %%
\begin{minipage}[c][1in]{\textwidth}%
\if@reportdraft%
{%
% Notice about preliminary document when ``draft'' is set
\hspace{0.55\textwidth}
\noindent\fbox{
\hspace*{\fill}\parbox{3.5in}{%
  \footnotesize\raggedright\textsf{%
  NOTICE: This document contains information of a preliminary nature and is not
  intended for release.  It is subject to revision or correction and therefore
  does not represent a final report.
}}\hspace*{\fill}%
}%
}
\else%
{%
  \hspace*{0pt}%
}%
\fi%
\end{minipage}%
%

\end{titlepage}
\restoregeometry
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% OSTI
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Email URL command
\newcommand{\email}[1]{\href{mailto:#1}{#1}}

% Create page
\def\makeostipage{%
\begin{titlepage}
  \centering\sffamily\small
  \fbox{\parbox{0.92\textwidth}{%
  \vspace{0.4cm}
    \begin{center}
      \textcolor{caslblue}{\textbf{DOCUMENT AVAILABILITY}} \\
    \end{center}
    \vspace{1cm}
Reports produced after January 1, 1996, are generally available free via US Department of Energy (DOE) SciTech Connect.

\begin{quote}
  \textbi{Website} \href{https://osti.gov/}{www.osti.gov}
\end{quote}

\vspace{0.5cm}

Reports produced before January 1, 1996, may be purchased by members of the
public from the following source:

\begin{quote}
	National Technical Information Service \\
	5285 Port Royal Road \\
	Springfield, VA 22161 \\
  \textbi{Telephone} 703-605-6000 (1-800-553-6847) \\
  \textbi{TDD}        703-487-4639 \\
	\textbi{Fax}        703-605-6900 \\
  \textbi{E-mail} \email{info@ntis.gov} \\
  \textbi{Website} \href{https://classic.ntis.gov/}{http://classic.ntis.gov}
\end{quote}

\vspace{0.5cm}

Reports are available to DOE employees, DOE contractors, Energy Technology Data
Exchange representatives, and International Nuclear Information System
representatives from the following source:

\begin{quote}
	Office of Scientific and Technical Information \\
	PO Box 62 \\
	Oak Ridge, TN 37831 \\
  \textbi{Telephone} 865-576-8401 \\
  \textbi{Fax} 865-576-5728 \\
  \textbi{E-mail} \email{reports@osti.gov} \\
  \textbi{Website} \href{https://osti.gov/contact}{https://www.osti.gov/} \\
\end{quote}
}}

\vspace{0.6cm}

\fbox{\parbox{0.91\textwidth}{
\vspace{0.4cm}
This report was prepared as an account of work sponsored by an agency of the
United States Government. Neither the United States Government nor any agency
thereof, nor any of their employees, makes any warranty, express or implied, or
assumes any legal liability or responsibility for the accuracy, completeness, or
usefulness of any information, apparatus, product, or process disclosed, or
represents that its use would not infringe privately owned rights. Reference
herein to any specific commercial product, process, or service by trade name,
trademark, manufacturer, or otherwise, does not necessarily constitute or imply
its endorsement, recommendation, or favoring by the United States Government or
any agency thereof. The views and opinions of authors expressed herein do not
necessarily state or reflect those of the United States Government or any agency
thereof.
    
\vspace{0.4cm}    
}}

% \vspace*{0.4cm}

\end{titlepage}
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% TITLE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand\maketitlepage{%
\begin{titlepage}
\setcounter{page}{2}%

%%% REPORT NUMBER %%%
\raggedleft{\large\textbf{\@reportnum}}
\vspace{1in}

% VERA LOGO
\centering
\begin{figure}[h!]
    \centering
    \includegraphics[width=0.25\textwidth]{vera-logo.png}
\end{figure}
\vspace{1in}

%%% TITLE %%%
{\Large\textbf{\color{caslblue}{\MakeUppercase{{\@title}}}}}
\vspace{3\baselineskip}%

%%% TITLE %%%
\begin{tabular}[t]{c}%
  \@author%
\end{tabular}%

\vspace{\stretch{.5}}

Date Published: \@date

\vspace{\stretch{.5}}

Prepared by \\
OAK RIDGE NATIONAL LABORATORY \\
Oak Ridge, TN 37831-6283 \\
managed by \\
UT-Battelle, LLC \\
for the \\
US DEPARTMENT OF ENERGY \\
under contract DE-AC05-00OR22725

\end{titlepage}%
} % end \maketitlepage

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Set the page style, specifically footers
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\fancypagestyle{plain}{%
  \renewcommand{\headrulewidth}{0pt}%
  \fancyhf{}%
    \fancyfoot[L]{{\color{caslblue} V}irtual {\color{caslblue}E}nvironment for {\color{caslblue}R}eactor {\color{caslblue}A}pplications}
    \fancyfoot[C]{\color{caslblue} \thepage{}}
    \fancyfoot[R]{{\color{black}\@reportnum}}%
}
\pagestyle{plain}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Revision Log
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand{\revisionlog}[5]{
\clearpage
\makeatletter
\begin{center}
    {\huge \bf\@title\par}
\end{center}
\vspace{2cm}
\begin{center}
{\Large\bf Revision Log}
\end{center}

\vspace{-0.5cm}
\begin{center}
\begin{tabular}{p{0.1\linewidth} p{0.1\linewidth} p{0.15\linewidth} p{0.5\linewidth}}\\\hline
\bf{Revision} & \bf{Date} & \bf{Affected Pages} & \bf{Revision Description} \\\hline
#1\hline
\end{tabular}
\end{center}

\vfill

\begin{center}
    {\Large\bf Document pages that are:}
    
    \vspace{-0.5cm}
    \begin{tabular}{ll}\\
    Export Controlled: & #2 \\
    IP/Proprietary/NDA Controlled: & #3 \\
    Sensitive Controlled: & #4 \\
    Unlimited: & #5 \\
    \end{tabular}
\end{center}

\vfill

\makeatother
\clearpage
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SIGNATURE PAGE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand{\signaturepagetwo}[2]{
\clearpage
\makeatletter
\begin{center}
    {\huge \bf\@title\par}
\end{center}
\vspace{2cm}
{\Large\bf Approvals:}

\vspace{2cm}
\begin{tabular}{ll}
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#1} & {\bf Date}\\[3cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#2} & {\bf Date}\\[3cm]
\end{tabular}
\makeatother
\clearpage
}

\newcommand{\signaturepagethree}[3]{
\clearpage
\makeatletter
\begin{center}
    {\huge \bf\@title\par}
\end{center}
\vspace{2cm}
{\Large\bf Approvals:}

\vspace{2cm}
\begin{tabular}{ll}
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#1} & {\bf Date}\\[3cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#2} & {\bf Date}\\[3cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#3} & {\bf Date}\\[3cm]
\end{tabular}
\makeatother
\clearpage
}

\newcommand{\signaturepagefour}[4]{
\clearpage
\makeatletter
\begin{center}
    {\huge \bf\@title\par}
\end{center}
\vspace{2cm}
{\Large\bf Approvals:}

\vspace{2cm}
\begin{tabular}{ll}
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#1} & {\bf Date}\\[3cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#2} & {\bf Date}\\[3cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#3} & {\bf Date}\\[3cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#4} & {\bf Date}\\[3cm]
\end{tabular}
\makeatother
\clearpage
}

\newcommand{\signaturepagefive}[5]{
\clearpage
\makeatletter
\begin{center}
    {\huge \bf\@title\par}
\end{center}
\vspace{2cm}
{\Large\bf Approvals:}

\vspace{1cm}
\begin{tabular}{ll}
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#1} & {\bf Date}\\[2.5cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#2} & {\bf Date}\\[2.5cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#3} & {\bf Date}\\[2.5cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#4} & {\bf Date}\\[2.5cm]
\makebox[3.5in]{\hrulefill} & \makebox[2.0in]{\hrulefill}\\
{\bf#5} & {\bf Date}\\[2.5cm]
\end{tabular}
\makeatother
\clearpage
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% FRONT MATTER
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newif\if@mainmatter
\@mainmattertrue
\def\@cleariffrontmatter{\if@mainmatter\relax\else{\clearpage}\fi}
\def\@cleardbliffrontmatter{\if@mainmatter\relax\else{\clearpage}\fi}

\newcommand\frontmatter{%
  \@mainmatterfalse%
  \renewcommand\and{\\}
  \renewcommand\thepage{Front cover}%
  \makecoverpage%
  \pagenumbering{roman}%
  \setcounter{page}{1}%
  \makeostipage%
  \maketitlepage%
  \cleardoublepage
  \setcounter{page}{3}%
}

% Abstract gets a new page if it's in the front matter; otherwise it's just at
% the top of the page.
\renewenvironment{abstract}{%
\if@mainmatter\relax\else
  \cleardoublepage
	\pagenumbering{arabic}
	\setcounter{page}{1}
\fi
	\addcontentsline{toc}{section}{\ornltmabstractname}
	\phantomsection
  \section*{\ornltmabstractname}%
}{}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% TABLE OF CONTENTS, LIST OF FIGURES, LIST OF TABLES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Clear the page before TOC if it is in the ``front matter''
\AtBeginDocument{%
\let\@origcfttoc\tableofcontents
\renewcommand\tableofcontents{%
\@cleardbliffrontmatter
\@origcfttoc%
}%
}

% Lists should have plain numbering if in the front matter
\renewcommand\@cfttocstart{%
  \if@mainmatter%
    \relax%
  \else%
    \thispagestyle{plain}%
  \fi%
}

% Lists should clear the page after if in front matter
\renewcommand\@cfttocfinish{\@cleariffrontmatter}

% Add section titles for figures/tables
\renewcommand\cftlofprehook{%
\phantomsection\addcontentsline{toc}{section}{\ornltmlofname}%
}
\renewcommand\cftlotprehook{%
\phantomsection\addcontentsline{toc}{section}{\ornltmlotname}%
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ACRONYMS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\setacronymstyle{long-short}
\setglossarystyle{long}
\renewcommand\glsdescwidth{\linewidth}
\glstoctrue
\renewcommand\glossarypostamble{\@cleardbliffrontmatter}
\renewcommand\acronymname{ACRONYMS}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% MAIN MATTER
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand\mainmatter{%
  %\cleardoublepage%
  \@mainmattertrue%
  \pagenumbering{arabic}%
  % Don't break the first section in order to allow ``mainmatter'' abstracts to
  % work correctly.
  \renewcommand{\sectionbreak}{\renewcommand\sectionbreak\clearpage}
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% CAPTION STYLES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[font=bf,labelsep=period]{caption}

% Caption with more than one sentence: the first sentence is the first argument,
% the rest are the second. This allows table of contents to just show the first
% sentence but display the whole thing in the text. It also clears the boldface
% from the second 
\newcommand\longcaption[2]{\caption[#1]{#1 \normalfont #2}}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\endinput
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% end of vera-ornltm.cls
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

