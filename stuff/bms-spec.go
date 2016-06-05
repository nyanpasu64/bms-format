let endian = big


func thread(addr) {
	var notes[8]	// which pitch to turn off?
	            	// 1..7

	Loop: for {
		switch ev {

		// **** CHILD THREAD
		case 0xC1:
			u8  track_id
			u24 addr

		// **** RETURN
		case 0xFF:
			break Loop

/*
		// **** CALL STACK
		// call function
		case 0xC3:
			u24 addr
			call addr

		// return function
		case 0xC5:
			// CONFLICT!!!!
			return stack	// V3
			drop 3      	// V2
*/

		// **** NOTES

		// Note on
		case ev < 0x80:
			u8 poly_id
			var note = ev
			u8 velocity

			note_on(note, velocity)
			notes[poly_id] = note

		// Note off
		case 0x81 <= ev < 0x88:
			var note = notes[ev % 8]
			note_off(note)

		// arookas
		// Repeat previous note?
		case 0xD4:
			u8 poly_id
			note_on(notes[poly_id])


		// **** DELAY (TIE)

		case 0x80:
			u8 delay

		case 0x88:
			u16 delay

		case 0xEA:
			u24 delay	// arookas

		case 0xCF:
			          	// arookas
			u8 unknown	// yoshimaster96

		case 0xF0:
			vlq tie		// 0b 1xxxxxxx 0xxxxxxx big-endian


		// **** INSTRUMENTS

		case 0xA4: drop 2	// [arookas] u8 instr_type, u8 value
		                 	// 0x20 = bank, 0x21 = patch
		                 	// 0x07 = ???

		case 0xAC: drop 3	// [arookas] u8 instr_type, u16 value


		// "Performances" (Arookas)

		enum BmsPerfType : u8 {
			VOLUME = 0,
			PITCH = 1,
			UNKNOWN = 2,	// UNKNOWN
			PAN = 3
			UNKNOWN = 4
		}

		// **** CONTROLS

		// Control change
		// u8 cctype, [layout/4] value, [layout%4] duration
		// See bms.py... It may or may not be easier to read.

		//        duration
		//  val | 0    ?    u8   u16  
		// -----+---- ---- ---- ----- 
		//  u8  | 94   95   96   97   
		//  s8  | 98   99   9a   9b   
		//  s16 | 9c   9d   9e   9f   

		u8 BmsPerfType, type value:
		type = switch ev {
			0x94: u8
			0x98: s8
			0x9C: s16
		}

		0x95, 0x99, 0x9D:
			unknown

		u8 BmsPerfType, type value, u8 length:
		type = switch ev {
			0x96: u8
			0x9A: s8
			0x9E: s16
		}

		u8 BmsPerfType, type value, u16 length:
		type = switch ev {
			0x97: u8
			0x9B: s8
			0x9F: s16
		}


		// Control slide
		case 0x96:
			u8 BmsPerfType
			u8 value
			u8 length

		case 0x97:
			u8 	BmsPerfType
			u8 	value
			u16	length



		// Dynamics:

		case 0xDF:
			u8 dynamic
			u24 value

		// Remove dynamic
		case 0xE0:
			u8 dynamic
			// **** ERROR?
			// arookas          	1 byte
			// yoshimaster96    	2 bytes
			// yoshimaster96 old	3 bytes

		// Clear all
		case 0xE1:
			pass

		// **** TEMPO

		case 0xFD:
			u16 tempo	// bpm

		case 0xFE:
			u16 tickrate


		// **** LOOPING (arookas)

		// Call, Jump
		case 0xC4, 0xC8:
			u8 BmsSeekMode
			u24 addr

		// "WriteBack"
		case 0xC6:
			u8 BmsSeekMode


		// UNKNOWN COMMANDS

		case 0xB1:
			u8 unknown
			u8 flag
			switch (flag) {
			case 0x40:
				drop 2
			case 0x80:
				drop 4
			}

		case 0xA0: drop 2
		case 0xA3: drop 2
		case 0xA5: drop 2
		case 0xA7: drop 2
		case 0xA9: drop 4
		case 0xAA: drop 4
		case 0xAD: drop 3
		case 0xB8: drop 2
		case 0xC2: drop 1
		case 0xC7: drop 4
		case 0xCB: drop 2
		case 0xCC: drop 2
		case 0xD0: drop 2
		case 0xD1: drop 2
		case 0xD2: drop 2
		case 0xD5: drop 2
		case 0xD8: drop 3
		case 0xDA: drop 1
		case 0xDB: drop 1
		case 0xDD: drop 3
		case 0xDF: drop 4
		case 0xE0: drop 2
		case 0xE2: drop 1
		case 0xE3: drop 1
		case 0xE6: drop 2	// CONFLICT - AROOKAS is WRONG!
		case 0xE7: drop 2	// Track Init
		case 0xEF: drop 3
		case 0xF1: drop 1
		case 0xF4: drop 1
		case 0xF9: drop 2

		default:
			log
		}
	}
}
