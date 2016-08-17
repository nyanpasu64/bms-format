#!/bin/bash

# **** UTIL ****

mkarc() {
	wszst create --overwrite --dest "$2" "$1"
}



# **** Dragon Roost BMS to JaiSeqs ****

orig=~/code/bms-sequencer	# orig=`pwd`
tree=~/ROMS/lozww
jaiseqsEx=$tree/jaiseqs/JaiSeqs.d

pushd $orig
	cp i_ryu.out.bms $jaiseqsEx/i_ryu.bms
popd


# **** JaiSeqs to DvdRoot ****

dvdroot=$tree/lozww.f/P-GZLE/files

# I... I really don't know how to make this less ugly... :'(
pushd $jaiseqsEx/..
	mkarc $jaiseqsEx JaiSeqs.arc
	# cp JaiSeqs.arc $dvdroot/Audiores/Seqs/
popd

# cp $orig/i_ryu.out.bms $bmsroot/i_ryu.bms

