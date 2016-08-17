
# **** UTIL ****

# q=`pwd`
# qd() {
# 	qq=`readlink -f "$1"`
# 	cd "$q"
# 	q=$qq
# }
# # $q is next folder

# pd = push directory
# $p = previous directory
p=`pwd`
pd() {		# Stores previous folder in $p.
	p=`pwd`
	cd $1
}

mkarc() {
	wszst create --overwrite --dest "$2" "$1"
}

# **** Dragon Roost BMS to JaiSeqs ****

tree=~/ROMS/lozww

pd ~/code/bms-sequencer
pd $tree/jaiseqs/JaiSeqs.d
	cp $p/i_ryu.out.bms i_ryu.bms

# **** Build JaiSeqs
pd ..
mkarc $p JaiSeqs.arc

# I... I really don't know how to make this less ugly... :'(
pushd $jaiseqsEx/..
	
	# cp JaiSeqs.arc $dvdroot/Audiores/Seqs/
popd

# cp $orig/i_ryu.out.bms $bmsroot/i_ryu.bms

