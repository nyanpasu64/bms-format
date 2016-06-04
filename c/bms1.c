#include <stdio.h>

int notes[8];
int tracknum=0;
int delay=0;
int tracksz[16]={0};

void dtime(FILE * ftemp) {
	if(delay<=0x7F)
	{
		putc(delay,ftemp);
		tracksz[tracknum]+=4;
	}
	else if(delay<=0x3FFF)
	{
		putc(0x80+(delay>>7),ftemp);
		putc(delay&0x7F,ftemp);
		tracksz[tracknum]+=5;
	}
	else if(delay<=0x1FFFFF)
	{
		putc(0x80+(delay>>14),ftemp);
		putc(0x80+((delay>>7)&0x7F),ftemp);
		putc(delay&0x7F,ftemp);
		tracksz[tracknum]+=6;
	}
	else if(delay<=0xFFFFFFF)
	{
		putc(0x80+(delay>>21),ftemp);
		putc(0x80+((delay>>14)&0x7F),ftemp);
		putc(0x80+((delay>>7)&0x7F),ftemp);
		putc(delay&0x7F,ftemp);
		tracksz[tracknum]+=7;
	}
}

int main(int argc, char ** argv)
{
	FILE * fin = fopen(argv[1],"rb");
	FILE * ftemp = fopen("TEMP","wb");
	FILE * fout = fopen(argv[2],"wb");
start:
	fseek(fin,5*tracknum,SEEK_SET);
	int ev = getc(fin);					// GETC
	if(ev==0xC1)
	{
		fseek(fin,(5*tracknum)+2,SEEK_SET);							// GETC
		                                   							// skip track index

		long off = (getc(fin)<<16) + (getc(fin)<<8) + getc(fin);		// GETC
		fseek(fin,off,SEEK_SET);
		while(ev!=0xFF)
		{
			ev = getc(fin);				// GETC
			if(ev<0x80)    				// write note
			{
				dtime(ftemp);

				putc(0x90,ftemp);		// note on
				int note = ev;
				putc(note,ftemp);
				int ppid = getc(fin);	// GETC
				notes[ppid]=note;
				int vol = getc(fin);		// GETC
				putc(vol,ftemp);
				delay=0;
			}
			else if(ev==0x80)			// tie u8
			{
				delay += getc(fin);		// GETC
			}
			else if(ev<0x88)			// note off
			{
				dtime(ftemp);

				putc(0x80,ftemp);		// note off
				int note = notes[ev&7];
				putc(note,ftemp);
				putc(0,ftemp);
				delay=0;
			}
			else if(ev==0x88)							// tie u16
			{
				delay += (getc(fin)<<8) + getc(fin);		// GETC
			}
			else if(ev==0x98) fseek(fin,2,SEEK_CUR);
			else if(ev==0x9A) fseek(fin,3,SEEK_CUR);
			else if(ev==0x9C) fseek(fin,3,SEEK_CUR);
			else if(ev==0x9E) fseek(fin,4,SEEK_CUR);
			else if(ev==0xA0) fseek(fin,2,SEEK_CUR);
			else if(ev==0xA3) fseek(fin,2,SEEK_CUR);
			else if(ev==0xA4) fseek(fin,2,SEEK_CUR);
			else if(ev==0xA5) fseek(fin,2,SEEK_CUR);
			else if(ev==0xA7) fseek(fin,2,SEEK_CUR);
			else if(ev==0xA9) fseek(fin,4,SEEK_CUR);
			else if(ev==0xAA) fseek(fin,4,SEEK_CUR);
			else if(ev==0xAC) fseek(fin,3,SEEK_CUR);
			else if(ev==0xAD) fseek(fin,3,SEEK_CUR);
			else if(ev==0xB1)
			{
				fseek(fin,1,SEEK_CUR);
				int flag = getc(fin);					// GETC
				if(flag==0x40) fseek(fin,2,SEEK_CUR);
				else if(flag==0x80) fseek(fin,4,SEEK_CUR);
			}
			else if(ev==0xB8) fseek(fin,2,SEEK_CUR);
			else if(ev==0xC2) fseek(fin,1,SEEK_CUR);
			else if(ev==0xC4) fseek(fin,4,SEEK_CUR);
			else if(ev==0xC5) fseek(fin,3,SEEK_CUR);
			else if(ev==0xC6) fseek(fin,1,SEEK_CUR);
			else if(ev==0xC7) fseek(fin,4,SEEK_CUR);
			else if(ev==0xC8) fseek(fin,4,SEEK_CUR);
			else if(ev==0xCB) fseek(fin,2,SEEK_CUR);
			else if(ev==0xCC) fseek(fin,2,SEEK_CUR);
			else if(ev==0xCF) fseek(fin,1,SEEK_CUR);
			else if(ev==0xD0) fseek(fin,2,SEEK_CUR);
			else if(ev==0xD1) fseek(fin,2,SEEK_CUR);
			else if(ev==0xD2) fseek(fin,2,SEEK_CUR);
			else if(ev==0xD5) fseek(fin,2,SEEK_CUR);
			else if(ev==0xDA) fseek(fin,1,SEEK_CUR);
			else if(ev==0xDB) fseek(fin,1,SEEK_CUR);
			else if(ev==0xDD) fseek(fin,3,SEEK_CUR);
			else if(ev==0xDF) fseek(fin,4,SEEK_CUR);
			else if(ev==0xE0) fseek(fin,3,SEEK_CUR);
			else if(ev==0xE6) fseek(fin,2,SEEK_CUR);
			else if(ev==0xE7) fseek(fin,2,SEEK_CUR);
			else if(ev==0xEF) fseek(fin,3,SEEK_CUR);
			else if(ev==0xF0)
			{
				int value = getc(fin);		// GETC
				while(value&0x80)
				{
					value=(value&0x7F)<<7;
					value+=getc(fin);		// GETC
				}
				delay += value;
			}
			else if(ev==0xF1) fseek(fin,1,SEEK_CUR);
			else if(ev==0xF4) fseek(fin,1,SEEK_CUR);
			else if(ev==0xF9) fseek(fin,2,SEEK_CUR);
			else if(ev==0xFD) fseek(fin,2,SEEK_CUR);
			else if(ev==0xFE) fseek(fin,2,SEEK_CUR);
		}
		putc(0,ftemp);
		putc(0xFF,ftemp);
		putc(0x2F,ftemp);
		putc(0,ftemp);
		tracksz[tracknum]+=4;
		tracknum++;
		goto start;
	}
	fclose(fin);
	fclose(ftemp);

	// **** write file

	ftemp = fopen("TEMP","rb");
	putc('M',fout);
	putc('T',fout);
	putc('h',fout);
	putc('d',fout);
	putc(0,fout);
	putc(0,fout);
	putc(0,fout);
	putc(6,fout);
	putc(0,fout);
	putc(1,fout);
	putc(0,fout);
	putc(tracknum,fout);
	putc(0,fout);
	putc(120,fout);
	for(int i=0; i<tracknum; i++)
	{
		putc('M',fout);
		putc('T',fout);
		putc('r',fout);
		putc('k',fout);
		putc(0,fout);
		putc((tracksz[i]&0xFF0000)>>16,fout);
		putc((tracksz[i]&0xFF00)>>8,fout);
		putc(tracksz[i]&0xFF,fout);
		for(int j=0; j<tracksz[i]; j++)
		{
			int w = getc(ftemp);		// GETC
			putc(w,fout);
		}
	}
	fclose(fout);
	fclose(ftemp);
	return 0;
}