#!/usr/bin/perl -w
use Try::Tiny;
use strict;
use warnings;
use Device::SerialPort;
use Digest::CRC;
use POSIX qw(strftime);


#Output Options
my $showRaw   = 1;
my $showDebug = 1;


#Init Serial Port
my $serial = Device::SerialPort->new("/dev/ttyUSB0");
$serial->baudrate(9600);
$serial->databits(8);
$serial->stopbits(1);
$serial->parity("none");
$serial->purge_all();
$serial->rts_active(0);
$serial->dtr_active(0);	
my($ser_count_in, $ser_bytes_in) = $serial->read(1);


#Variablen
my @DetectStart = (0..7);
my @RxBuffer = (0..10000);
my $FrameRxCTR = 0;
my $FrameCRC = 0;
my $FramePos = 0;
my $deep = 0;
my @res;
my %obis = ();
my $ctx = Digest::CRC->new(width=>16, init=>0xffff, xorout=>0xffff, refout=>1, poly=>0x1021, refin=>1, cont=>0);
my $crc;
my $sleepS;


#Subroutinen
sub getType {
	if(substr(sprintf("%02x", $RxBuffer[$FramePos]), 0, 1) == "7") {
		print(('   ' x $deep)."A - ") if($showDebug);
		return 0;
	} else {
		print(('   ' x $deep)."S - ") if($showDebug);
		return 1;
	}
}

sub getString {
	my $len = hex(substr(sprintf("%02x", $RxBuffer[$FramePos]), 1, 1));
	#TBD: If 0x8x, second byte also contain length
	$FramePos++;
	my $i = 1;
	my $lStr = "";
	while($i < $len) {
		$lStr .= sprintf("%02x ", $RxBuffer[$FramePos]);
		$i++;
		$FramePos++;
	}
	print(($len-1) . ": " .$lStr."\n") if($showDebug);
	return $lStr;
}

sub getArray {
	$deep++;
	my $len = hex(substr(sprintf("%02x", $RxBuffer[$FramePos]), 1, 1));
	#TBD: If 0xfx, second byte also contain length
	$FramePos++;
	print("LEN".$len."\n") if($showDebug);
	my @lArray = ();
	
	my $i = 0;
	while($i < $len) {
		if(getType() == 0) {
			push(@lArray, getArray());
		} else {
			push(@lArray, getString());
		}
		$i++;
	}
	
	if($deep==5) {
		if(substr($lArray[0], 6, 2) eq "60") {
			$obis{substr($lArray[0], 6, 8)} = $lArray[5];
		} else {
			$lArray[5] =~ s/ //ig;
			$lArray[4] =~ s/ //ig;
			my $expo = hex($lArray[4]);
			if($expo > 128) {$expo -= 256;}
			$obis{substr($lArray[0], 6, 8)} = hex($lArray[5]) * (10 ** $expo);
		}	
	}
	
	$deep--;
	return @lArray;
}


#MAIN
print "Starting\n";
while(1) { #Main Loop
	do { #CRC Loop
		do { #Wait for start Frame
			($ser_count_in, $ser_bytes_in) = $serial->read(1);
			if ($ser_count_in != 0) {
				$DetectStart[7] = $DetectStart[6];
				$DetectStart[6] = $DetectStart[5];
				$DetectStart[5] = $DetectStart[4];
				$DetectStart[4] = $DetectStart[3];
				$DetectStart[3] = $DetectStart[2];
				$DetectStart[2] = $DetectStart[1];
				$DetectStart[1] = $DetectStart[0];
				$DetectStart[0] = ord($ser_bytes_in);
			}
		} until (
			($DetectStart[7] == 0x1B)
			&&
			($DetectStart[6] == 0x1B)
			&&
			($DetectStart[5] == 0x1B)
			&&
			($DetectStart[4] == 0x1B)
			&&
			($DetectStart[3] == 0x01)
			&&
			($DetectStart[2] == 0x01)
			&&
			($DetectStart[1] == 0x01)
			&&
			($DetectStart[0] == 0x01)
		);
		print "1of4 Framestart";

		$ctx->reset(width=>16, init=>0xffff, xorout=>0xffff, refout=>1, poly=>0x1021, refin=>1, cont=>0);
		$ctx->add(chr(0x1b),chr(0x1b),chr(0x1b),chr(0x1b));
		$ctx->add(chr(0x01),chr(0x01),chr(0x01),chr(0x01));
		$FrameRxCTR = 0;
	
		do { #Wait for end Frame
			($ser_count_in, $ser_bytes_in) = $serial->read(1);
			if ($ser_count_in != 0) {
				$DetectStart[4] = $DetectStart[3];
				$DetectStart[3] = $DetectStart[2];
				$DetectStart[2] = $DetectStart[1];
				$DetectStart[1] = $DetectStart[0];
				$DetectStart[0] = ord($ser_bytes_in);
				$ctx->add($ser_bytes_in);
				$RxBuffer[$FrameRxCTR] = ord($ser_bytes_in);
				$FrameRxCTR++;
			}
		} until (
			($DetectStart[4] == 0x1B)
			&&
			($DetectStart[3] == 0x1B)
			&&
			($DetectStart[2] == 0x1B)
			&&
			($DetectStart[1] == 0x1B)
			&&
			($DetectStart[0] == 0x1A)
		);
		print " / 2of4 Frameende";
	
		$FrameCRC = $FrameRxCTR;
		do { #Read CRC Bytes
			($ser_count_in, $ser_bytes_in) = $serial->read(1);
			if ($ser_count_in != 0) {
				$RxBuffer[$FrameRxCTR] = ord($ser_bytes_in);
				$FrameRxCTR++;			
			}
		} until ($FrameRxCTR >= $FrameCRC + 3);
		$ctx->add(chr($RxBuffer[$FrameRxCTR-3]));
		print " / 3of4 Empfangene Bytes: ".($FrameRxCTR + 8);
		
		$crc = $ctx->hexdigest;
		printf(" / 4of4 CRC: %02x%02x = %s", $RxBuffer[$FrameRxCTR-1], $RxBuffer[$FrameRxCTR-2], $crc);
		if($crc eq sprintf("%02x%02x",$RxBuffer[$FrameRxCTR-1], $RxBuffer[$FrameRxCTR-2])) {
			print " -> OK\n";
		} else {
			print " -> ERROR\n";
		}
	} until ($crc eq sprintf("%02x%02x",$RxBuffer[$FrameRxCTR-1], $RxBuffer[$FrameRxCTR-2]));


	if($showRaw) {
		for ($FramePos=0; $FramePos < $FrameRxCTR; $FramePos++) {
			printf("%02x ", $RxBuffer[$FramePos]);
		}
		print "\n";
	}

	$FramePos = 0;
	print("SML Part 1 - ") if($showDebug);
	@res = getArray();
	print("SML Part 2 - ") if($showDebug);
	@res = getArray();
	print("SML Part 3 - ") if($showDebug);
	@res = getArray();
	
	print("OBIS Extract:\n");
	foreach my $i (sort keys %obis) {
		print($i." = ".$obis{$i}."\n");
	}


	$sleepS = 60 - strftime("%S", localtime);
	print "Sleep: " . $sleepS . " seconds\n";
	sleep($sleepS);
} #END Main Loop
