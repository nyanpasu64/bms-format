#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

shopt -s expand_aliases

if $(uname -s | grep -qi cygwin); then
	echo cygwin
	HOME=/cygdrive/c/users/nyanpasu64
	# it appears that wszst is incompatible with cygwin directory symlinks
	# maybe because they're special files
	alias ahk='cygstart --wait'

elif $(uname -s | grep -qi msys); then
	echo msys
	HOME=/c/users/nyanpasu64
	alias ahk=start

else
	echo native
	echo Not recommended, as AutoHotkey + GCRebuilder doesn\'t work properly on Linux.
	exit
fi

# $p = previous directory
# pd = push directory
p=`pwd`
pd() {
	p=`pwd`
	cd $1
}

mkarc() {
	wszst create --overwrite --dest "$2" "$1"
}


# **** Dragon Roost BMS to JaiSeqs ****

pd ~/code/bms-sequencer
code=`pwd`
pd ~/ROMS/lozww/JaiSeqs.d
	cp $p/i_ryu.out.bms i_ryu.bms

# **** Build JaiSeqs
pd ..
	mkarc $p JaiSeqs.arc

pd $code/ahk
ahk patch.ahk

echo Done!
