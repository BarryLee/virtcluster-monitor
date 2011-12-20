#!/usr/bin/perl
#
# script to log CPU stats for VMs 
#
# contact: John Lim jlim#natsoft.com
# (c) 2009 John Lim. Released under BSD License.
#
# Syntax:
#    perl xenstat.pl [$mode] [$intervalsecs=5] [$nsamples=0] [$urlToPostStats]
#
# Original src: http://lists.xensource.com/archives/html/xen-users/2005-06/msg00139.html
#
#
# Usage 
# -----
#  perl xenstat.pl          -- generate cpu stats every 5 secs
#  perl xenstat.pl 10       -- generate cpu stats every 10 secs
#  perl xenstat.pl 5 2      -- generate cpu stats every 5 secs, 2 samples
#
#  perl xenstat.pl d 3      -- generate disk stats every 3 secs
#  perl xenstat.pl n 3      -- generate network stats every 3 secs
#  perl xenstat.pl a 5      -- generate cpu avail stats every 5 secs
#
# Sample Output with "perl xenstat.pl 5"
# --------------------------------------
#  cpus=2
#  54_garuda     0.66%  1781.44 cpu sec in 3.14 days (2 vcpu,   750 M)
#  59_gyrfalcon 16.18%  4625.25 cpu sec in 0.33 days (2 vcpu,  2048 M)
#  Dom-0         3.12%  8474.89 cpu sec in 3.14 days (2 vcpu,   564 M)
#
#                        54_garu 59_gyrf   Dom-0    Idle
#  2009-09-29 01:03:22       4.1     0.2    15.7    80.0 *
#  2009-09-29 01:03:27      12.2    23.1    14.2    60.5 ** 
#  2009-09-29 01:03:22       9.1     1.2    12.7    76.0 *
#
# We also graph the results: 
#   10%+ is 1 stars 
#   30%+ is 2 stars
#   50%+ is 3 stars
#   70%+ is 4 stars
#   90%+ is 5 stars
#
#
# $urlToPostStats
# ---------------
# If $urlToPostStats defined, e.g.
#
#  perl xenstat.pl 10 1 http://server/store.php
#
# then the following url is generated after 10s and called using wget:
#  http://server/store.php?$dom0=$cpu0&$dom1=$cpu1&$dom2=$cpu2
# 
#
#
# Network mode [n]
# ----------------
# Shows total network reads and writes in KBytes or MBytes for that
# time period.
#
# perl xenstat.pl n
#
#    Network I/O (K)  52_pyth 54_garu 59_gyrf   Dom-0
# 2009-10-05 19:55:08       7     979       1       3
# 2009-10-05 19:55:13       6    1.2M       1       1
# 2009-10-05 19:55:18       5     600       2       3
#
#
# Disk IO mode [d]
# ----------------
# Shows total reads and writes for each domain for that time period. 
#
# perl xenstat.pl d
#  
#  Disk I/O (Reqs)  52_pyth 54_garu 59_gyrf   Dom-0
# 2009-10-05 19:51:02       4       0    1.3k       0
# 2009-10-05 19:51:07      27       0    1.1k       0
#
#
#
# Available CPU mode [a]
# ----------------------
# Alternatively, you can view information in terms of Available CPU %.
# The advantage is that it tells when you hit the limit of CPU usage
# for a guest VM. In the example, note that garuda has only 1 vcpu
# which means that cpu available is capped at 50% for garuda. 
#
# Secondly, you know when you are running out of CPU resources, as
# the value for a domain will fall to zero.
#
# cpus=2
#     40_falcon   2.33%    2.53 cpu hrs  in 2.26 days (2 vcpu,  2048 M)
#     52_python   0.26%  940.55 cpu secs in 2.08 days (2 vcpu,  1500 M)
#   54_garuda_0   1.48%   18.47 cpu secs in 0.01 days (1 vcpu,   750 M)
#         Dom-0   2.28%    9.73 cpu hrs  in 8.89 days (2 vcpu,   564 M)
#
#    Available CPU %  40_falc 52_pyth 54_garu   Dom-0 CPU-free 
# 2009-10-04 17:22:36    99.8    99.9    50.0    86.3    86.0 *
# 2009-10-04 17:22:37    99.9   100.0    25.8    81.8    57.6 **
# 2009-10-04 17:22:39    99.8    99.9    44.0    80.8    74.6 *
# 2009-10-04 17:22:40    99.9   100.0    44.0    81.7    75.6 *
#
# xenstat a                      -- run every 5 secs
# xenstat a 1                    -- run every 1 sec
# xenstat a 10 5 http://server/  -- run every 10 sec, 5 samples, save to server
#
#
# LIMITATIONS
# -----------
# Now requires /usr/sbin/xentop and xen 3.1 or later.
#
# 0.7 6 Oct 2009
# Finetuned output of 'd' mode. 
# 
# 0.6 5 Oct 2009
# Added [a] mode.
# Now requires xentop and only works with Xen 3.1 or later. This gives more reliable
#   cpu % readings.
# Ideas from http://pookey.co.uk/blog/archives/53-Monitoring-Xen-via-SNMP-update.html
#
# 0.5 4 Oct 2009
# Added "xenstat.pl d" disk stats and "xenstat.pl n" for network stats
# 
# 0.5 4 Oct 2009
# Added to hdr mem info and changed to display cpu days/hrs/secs as appropriate
# Reenabled strict.
# Removed hires timer. No improvement in accuracy.
#
# 0.4  2 Oct 2009
# Added graphing of CPU used.
#
# 0.3  
# Sleep interval can change wrongly due to $interval set wrongly. Fixed.
#
# 0.2  1 Oct 2009
# Works correctly when guest vm is started or shutdown.
# Fixed reboot handling - cpu usage will go negative
# Changed Domain-0 to Dom-0.
# Change cpu formating from %3d to %7.1f.
# Added domain names every 20 lines.
# Switched to hires sleep timer.
# Added display of vcpu
#
# 0.1  29 Sep 2009
# Fixed bugs & modified to support wget by John Lim 
#

use strict;
use POSIX qw(floor);
use Time::HiRes qw(sleep time);


my $WGET = '/usr/bin/wget';
my $XENTOP = '/usr/sbin/xentop';
my $XM = '/usr/sbin/xm';

unless(-e $XENTOP) {
	print "$XENTOP not found\n";
	die;
}

###############
# subroutines
###############

sub URLEncode {
    my $theURL = $_[0];
    $theURL =~ s/([\W])/"%" . uc(sprintf("%2.2x",ord($1)))/eg;
    return $theURL;
}

# trims leading and trailing whitespace
sub trim($)
{
  my $string = shift;
  $string =~ s/^\s+//;
  $string =~ s/\s+$//;
  return $string;
}

#################
# Parse params
#################
my $mode = 'c';  # can be 'd' for disk or 'n' network
my $idling = shift || 5;
my $intervalsecs = $idling;
if ($idling =~ /[adn]/i) {
  if ($idling eq 'd') {
    $idling = 0;
    $mode = 'd';
  } elsif ($idling eq 'n') {
    $idling = 0;
    $mode = 'n'
  }
  $intervalsecs = shift || 5;
}else {
  $idling = 0;
}
if ($intervalsecs < 1) {$intervalsecs = 1;}

my $num_samples = shift || 0;
my $url = shift || '';

###############
# Setup vars
###############
my $starsinc = 20;
my $lastinterval = $intervalsecs;
my $uptime = `cat /proc/uptime`;
$uptime =~ s/ .*$//g; # trim from first space, should leave us uptime in secs

my $proc = `sudo $XM info | grep nr_cpu`;
my ($ncpus) = ($proc =~ m/.*(\d+)/);
if ($ncpus == 0) {$ncpus = 1;}

if ($mode eq 'c') {
  print "cpus=$ncpus\n";
}

my $loop = 0;
my $lastcount = -1;
my $lasttime = time();

# offsets to xenInfo
my $zsec = 2;
my $zcpu = 3;
my $zmem = 4;
my $zvcpu = 8;
my $znwr = 10;
my $znrd = 11;
my $zrd = 14;
my $zwr = 15;

RESTART:

###############################
# get uptimes for each guest VM
###############################
my @domuptime =();
my $dat = `sudo $XM list -l`
      or die "no output from $XM list ?? maybe it isn't in your path?";
$dat =~ tr/\(\)/{}/;  # for readability of regex below.

while ( my($dom,$rest) = ($dat =~ m/^(.*?\n})(.*)$/gs ) ) {
      my ($domcpu) = ($dom =~ m/{cpu_time\s+([\d\.]+)}/);
      my ($domup) = $uptime;
      ($domup) = ($dom =~ m/{start_time\s([\d\.]+)}/);
      if ($domup == 0) {
          $domup =$uptime;
      } else {
        $domup = time() - $domup;
      }
      push(@domuptime, $domup);
      $dat = $rest;
}
  


my $printhdr  = 1;
my $interval = 0.1;
my %lastcpu = ();
my @doma = ();
my @vcpus = ();
my @prevcpa = ();

##############################
# Get statistics using xentop
##############################
while ( ++$loop ) { # loop forever
   my $buf = '';
   my $count = 0;
   my @result = split(/\n/, `sudo $XENTOP -b -i 2 -d$interval`);
  $interval = $intervalsecs;
  # remove the first line
  shift(@result);
  shift(@result) while @result && $result[0] !~ /^[\t ]+NAME/;
  shift(@result);

   my $curtime = time();
   my @cpa = ();
   my $urlget = $url .'?';
   my $totcpu = 0;

   my ($sec,$min,$hour,$mday,$mon,$year,$wday,
   $yday,$isdst)=localtime($curtime);
   if (!$printhdr) {
        $buf = sprintf "%4d-%02d-%02d %02d:%02d:%02d",
                 $year+1900,$mon+1,$mday,$hour,$min,$sec;
   }
  $count = 0;
  foreach my $line (@result)
  {
    my @xenInfo = split(/[\t ]+/, trim($line));
    my $o = 0;
    if ($xenInfo[6] eq 'no') {$o = 1};

    my $notused = sprintf("%16s, cpusec: %8d, cpu%%: %5.2f, vbd_rd: %8d, vbd_wr: %8d\n",
    $xenInfo[0],
    $xenInfo[$zsec],
    $xenInfo[$zcpu],
    $xenInfo[$zrd+$o],
    $xenInfo[$zwr+$o]
    );
   if ($xenInfo[0] eq 'Domain-0') {$xenInfo[0]='Dom-0';}
    if ($mode eq 'c') {
      push(@cpa, $xenInfo[$zcpu]);
    } elsif ($mode eq 'n') {
      push(@cpa, $xenInfo[$znrd+$o]+$xenInfo[$znwr+$o]);
    } elsif ($mode eq 'd') {
      push(@cpa, $xenInfo[$zrd+$o]+$xenInfo[$zwr+$o]);
    }
    push(@vcpus, $xenInfo[$zvcpu+$o]);
    if ($printhdr) {
     	push(@doma, $xenInfo[0]);

	 my $cputime = $xenInfo[$zsec];
	 my $cput = $cputime;
         my $scale = 'secs';
	 if ($cputime > 86400) {
	   $scale = 'days';
	   $cput = $cputime / 86400;
	 } elsif ($cputime > 3600) {
	   $scale = 'hrs ';
   	   $cput = $cputime / 3600;
         }
	 my $up = @domuptime[$count];
	 if ($up == 0) {$up = $uptime;}
	 my $mem = $xenInfo[$zmem];
	 my $cpupct = $cputime/$up;
	 
	 my $upsc = 'days';
	 $up /= 86400;
	 if ($up > 366) {
		$up /= 365.25;
	        $upsc = 'yrs ';
    	 }
         if ($mode eq 'c') {
           $buf .= sprintf "%16s  %5.2f%% %7.2f cpu %s in %6.2f %s (%2d vcpu, %5d M)\n",
             $xenInfo[0], 100*$cpupct, $cput, $scale, $up, $upsc, $xenInfo[$zvcpu+$o],$mem/1024;
         }

    } 
    $count += 1;
  }

  if ($lastcount > 0 && $lastcount != $count) {
	if ($lastcount < $count) {
	  print "\nGuest VM started\n";
	} else {
	  print "\nGuest VM stopped\n";
	}
	$lastcount = $count;
	goto RESTART;
   }

   $lastcount = $count;
  
   if (!$printhdr) {

      my $tcpu = 0;
      my $i = 0;
      foreach my $c (@cpa) {
        $tcpu += $c/$ncpus;
      }
      my $fcpu = 100.0 - $tcpu;
      if (-0.1 < $fcpu && $fcpu <= 0.001) {$fcpu = 0.0;}
      foreach my $c(@cpa) {
        my $roundedcpu = $c/$ncpus;
	my $vcpu = $vcpus[$i];
        if ($idling) {
		my $mypct = 100*$vcpu/$ncpus-$roundedcpu;
		if ($mypct < 0.0) {$mypct = 0.0;}
		#if ($mypct > $fcpu) {$mypct = $fcpu;}
		$buf .= sprintf "%8.1f", $mypct;
	} elsif($mode eq 'c') {
		$buf .= sprintf "%8.1f", $roundedcpu;
	} else {
		my $pr = $c - $prevcpa[$i];
		$roundedcpu = $pr;
		my $k = 1000;
		if ($mode eq 'n' && $pr >= 1000) {
                  $pr /= 1000;
                  $buf .= sprintf " %6.1fM", $pr;
		}elsif ($mode eq 'd' && $pr >= 100000) { 
		    $pr /= 1000;
                    $buf .= sprintf " %6dk", $pr;
		} else {
                  $buf .= sprintf " %7d", $pr;
                }
        }
        if ($url) {
          my $domname = @doma[$i];
          $urlget .= URLEncode($domname) . '=' . (sprintf "%.1f",$roundedcpu).'\&';
        }
        $i += 1;
      }
      
      #if ($mode eq 'c') {
      #  $buf .= sprintf "%8.1f ", $fcpu;
      #  if ($starsinc) {
      #    my $stars = floor(($tcpu+($starsinc>>1))/$starsinc);
      #    while ($stars--) {
#	    $buf .= '*';
#          }
#        }
#      }

      if ($url) {
        $urlget .= "__mode=$mode\\&__interval=$intervalsecs";
        print "\n";
        `$WGET -O - $urlget`;
      }
   } 
   @prevcpa = @cpa;

   print "$buf\n";
   if ($loop % 20 == 0 || $printhdr) {
     if ($idling) {
        printf "%20s",'Available CPU %  ';
     } else {
	if ($mode eq 'c') {printf "%20s",'';}
        elsif ($mode eq 'n') {printf "%20s",'Network I/O (K)  ';}
        elsif ($mode eq 'd') {printf "%20s",'Disk I/O (Reqs)  ';}
     }
     
     for my $n (@doma) {
	printf "%8s", substr($n,0,7).' ';
     }
  
     if ($idling) {
       print "CPU-free\n";
     } elsif ($mode eq 'c') {
       print "   Idle\n";
     } else {
       print "\n";
     }
   }
   exit if ($num_samples && $loop > $num_samples);
   #sleep $intervalsecs;
   $printhdr = 0; 
}


