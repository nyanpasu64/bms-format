#include <stdio.h>

int notes[8];
int tracknum=0;
int delay=0;
int basedelay=0;
int tracksz[16]={0};
int savepos=0;
int inmain=1;

enum branch
{
	BR_NORMAL,
	BR_C1,
	BR_FF
};


void dtime(FILE * fout) {
	if(delay<=0x7F)
	{
		putc(delay,fout);
		tracksz[tracknum]+=4;
	}
	else if(delay<=0x3FFF)
	{
		putc(0x80+(delay>>7),fout);
		putc(delay&0x7F,fout);
		tracksz[tracknum]+=5;
	}
	else if(delay<=0x1FFFFF)
	{
		putc(0x80+(delay>>14),fout);
		putc(0x80+((delay>>7)&0x7F),fout);
		putc(delay&0x7F,fout);
		tracksz[tracknum]+=6;
	}
	else if(delay<=0xFFFFFFF)
	{
		putc(0x80+(delay>>21),fout);
		putc(0x80+((delay>>14)&0x7F),fout);
		putc(0x80+((delay>>7)&0x7F),fout);
		putc(delay&0x7F,fout);
		tracksz[tracknum]+=7;
	}
}


int parse_ev(FILE * fin, FILE * ftemp)
{
			printf("%06X\n", ftell(fin));
			int ev = getc(fin);
			if(ev<0x80)
			{
				dtime(ftemp);

				putc(0x90,ftemp);
				int note = ev;
				putc(note,ftemp);
				printf("at %06X\n", ftell(fin));
				int ppid = getc(fin);
				printf(" ppid %02X\n", ppid);
				notes[ppid]=note;
				int vol = getc(fin);
				putc(vol,ftemp);
				delay=0;
			}
			else if(ev==0x80)
			{
				if(inmain==1) basedelay+=getc(fin);
				else delay+=getc(fin);
			}
			else if(ev<0x88)
			{
				dtime(ftemp);

				putc(0x80,ftemp);
				int note = notes[ev&7];
				putc(note,ftemp);
				putc(0,ftemp);
				delay=0;
			}
			else if(ev==0x88)
			{
				if(inmain==1) {basedelay += (getc(fin)<<8) + getc(fin);}
				else {delay += (getc(fin)<<8) + getc(fin);}
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
				int flag = getc(fin);
				if(flag==0x40) fseek(fin,2,SEEK_CUR);
				else if(flag==0x80) fseek(fin,4,SEEK_CUR);
			}
			else if(ev==0xB8) fseek(fin,2,SEEK_CUR);
			else if(ev==0xC1) return BR_C1;
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
			else if(ev==0xD8) fseek(fin,3,SEEK_CUR); // NEW!
			else if(ev==0xDA) fseek(fin,1,SEEK_CUR);
			else if(ev==0xDB) fseek(fin,1,SEEK_CUR);
			else if(ev==0xDD) fseek(fin,3,SEEK_CUR);
			else if(ev==0xDF) fseek(fin,4,SEEK_CUR);
			else if(ev==0xE0) fseek(fin,2,SEEK_CUR); // WAS 3
			else if(ev==0xE2) fseek(fin,1,SEEK_CUR); // NEW!
			else if(ev==0xE3) fseek(fin,1,SEEK_CUR); // NEW!
			else if(ev==0xE6) fseek(fin,2,SEEK_CUR);
			else if(ev==0xE7) fseek(fin,2,SEEK_CUR);
			else if(ev==0xEF) fseek(fin,3,SEEK_CUR);
			else if(ev==0xF0)
			{
				int value = getc(fin);
				while(value&0x80)
				{
					value=(value&0x7F)<<7;
					value+=getc(fin);
				}
				if(inmain==1) basedelay += value;
				else delay += value;
			}
			else if(ev==0xF1) fseek(fin,1,SEEK_CUR);
			else if(ev==0xF4) fseek(fin,1,SEEK_CUR);
			else if(ev==0xF9) fseek(fin,2,SEEK_CUR);
			else if(ev==0xFD) fseek(fin,2,SEEK_CUR);
			else if(ev==0xFE) fseek(fin,2,SEEK_CUR);
			else if(ev==0xFF) return BR_FF;
			return BR_NORMAL;
}

int main(int argc, char ** argv)
{
	FILE * fp = fopen(argv[1],"rb");
	FILE * ftemp = fopen("TEMP","wb");
	FILE * fp2 = fopen(argv[2],"wb");
	while(true)
	{
		int status = parse_ev(fp,ftemp);
		if(status==BR_NORMAL);
		else if(status==BR_C1)
		{
			fseek(fp,1,SEEK_CUR);
			long offset = (getc(fp)<<16) + (getc(fp)<<8) + getc(fp);
			savepos=ftell(fp);
			fseek(fp,offset,SEEK_SET);
			inmain=0;
		}
		else if(status==BR_FF)
		{
			if(inmain==1) break;
			else
			{
				tracksz[tracknum]+=4;
				putc(0,ftemp);
				putc(0xFF,ftemp);
				putc(0x2F,ftemp);
				putc(0,ftemp);
				delay=basedelay;
				fseek(fp,savepos,SEEK_SET);
				tracknum++;
				inmain=1;
			}
		}
	}
	fclose(fp);
	fclose(ftemp);
	ftemp = fopen("TEMP","rb");
	putc('M',fp2);
	putc('T',fp2);
	putc('h',fp2);
	putc('d',fp2);
	putc(0,fp2);
	putc(0,fp2);
	putc(0,fp2);
	putc(6,fp2);
	putc(0,fp2);
	putc(1,fp2);
	putc(0,fp2);
	putc(tracknum,fp2);
	putc(0,fp2);
	putc(120,fp2);
	for(int i=0; i<tracknum; i++)
	{
		putc('M',fp2);
		putc('T',fp2);
		putc('r',fp2);
		putc('k',fp2);
		putc(0,fp2);
		putc((tracksz[i]&0xFF0000)>>16,fp2);
		putc((tracksz[i]&0xFF00)>>8,fp2);
		putc(tracksz[i]&0xFF,fp2);
		for(int j=0; j<tracksz[i]; j++)
		{
			int w = getc(ftemp);
			putc(w,fp2);
		}
	}
	fclose(fp2);
	fclose(ftemp);
	return 0;
}
