# extrapkgs.sh - extra packages to include in createvm -
# using Joe's Excellent vHosting framework (EVH Framework?!) for KVM, etc
# copyright (c) 2007-11 Joseph J Wolff

# trac stuff

extra=" --addpkg trac \
  --addpkg trac-git \
  --addpkg trac-mercurial \
  --addpkg python-clearsilver \
  --addpkg python-textile \
  --addpkg trac-spamfilter \
  --addpkg trac-bzr "
