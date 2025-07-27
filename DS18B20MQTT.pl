#!/usr/bin/perl
#
# MQTT login with password but without ssl:
# export MQTT_SIMPLE_ALLOW_INSECURE_LOGIN=true
#
use warnings;
use strict;

use Try::Tiny;
use Net::MQTT::Simple;

# Configuration
my $general_delay = 20;

my $mqtt_host = "mqtt_host";
my $mqtt_topic = "DS18B20";
my $mqtt_username = "mqtt_username";
my $mqtt_password = "mqtt_password";

my $ds18b20_count = 5;
my $ds18b20_file = '/sys/bus/w1/devices/w1_bus_master1/w1_master_slaves';

# Internal Variables
our @ds18b20_list=();
our %ds18b20_last=();
our %ds18b20_current=();

sub getList {
    open my $ds18b20_handler, $ds18b20_file or die "Could not open $ds18b20_file: $!";
    while( my $line = <$ds18b20_handler>)  { 
        $line =~ s/^\s+|\s+$//g;
        if( $line =~ /28-/ ) {
            if (grep { $_ eq $line } @ds18b20_list) {
                print "Device already exists: " . $line . "\n";
            } else {
                print "New Device: " . $line . "\n";
                push(@ds18b20_list, $line);
            }
        }
    }
    close $ds18b20_handler;
}

sub getValue {
    my $sensor = $_[0];
    try {
        open my $ds18b20_handler, '/sys/bus/w1/devices/' . $sensor . '/w1_slave';
        my $line = <$ds18b20_handler>;
        if ($line=~/YES$/) {
            $line = <$ds18b20_handler>;
            if ($line=~/=(\d+)$/) {
                my $td = $1;
                $td /= 1000.0;
                close $ds18b20_handler;
                return $td
            } else {
                close $ds18b20_handler;
                return -99;
            }
        } else {
            close $ds18b20_handler;
            return -99;
        }
    } catch {
        return -99;
    };
}

# MQTT Init
print "01. Connecting to MQTT\n";
my $mqtt = Net::MQTT::Simple->new($mqtt_host);
$mqtt->login($mqtt_username, $mqtt_password);

# Get ALL Sensores
print "02. Get device list\n";
while($#ds18b20_list < ($ds18b20_count -1)) {
    getList();
    if($#ds18b20_list < ($ds18b20_count -1)) {
        print "Too less devices: " . ($#ds18b20_list + 1) . " of " . $ds18b20_count . "\n";
        sleep(5);
    }
}

#Main Loop
print "03. Starting main-loop\n";
while(1) {
    foreach (@ds18b20_list) {
        my $sensor = $_;
        my $i = getValue($sensor);
        if($i > -99) {
            $ds18b20_current{$sensor} = $i;
            if (!exists $ds18b20_last{$sensor}) {
                $ds18b20_last{$sensor} = 99999;
            }
            if ($ds18b20_current{$sensor} != $ds18b20_last{$sensor}) {
                print "Value changed: " . $sensor . " = " . $ds18b20_current{$sensor} . "\n";
                $mqtt->retain($mqtt_topic . "/" . $_ => $ds18b20_current{$sensor});
                $ds18b20_last{$sensor} = $ds18b20_current{$sensor};
            }
        }
    }
	sleep($general_delay);
}
