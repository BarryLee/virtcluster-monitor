#!/usr/bin/perl
#
# script to dump CPU stats for VMs
#
# vim:ai

use strict;

my $interval = shift || 5;
my $num_samples = shift || 0;

my $uptime = `cat /proc/uptime`;
$uptime =~ s/ .*$//g; # trim from first space, should leave us uptime in secs

my $XM="/usr/sbin/xm";


my $loop = 0;
my $lasttimestamp = 0;
my %lastcpu = ();
while ( ++$loop ) { # loop forever
   my $buf = '';
   my $count = 0;
   my $dat = `sudo $XM list -l`
      or die "no output from $XM list ?? maybe it isn't in your path?";
   my $datatimestamp = time();
   $dat =~ tr/\(\)/{}/;  # for readability of regex below.
   my $totcpu = 0;

   while ( my($dom,$rest) = ($dat =~ m/^(.*?\n})(.*)$/gs ) ) {
      my ($domcpu) = ($dom =~ m/{cpu_time\s([\d\.]+)}/)
         or die "couldn't extract cpu_time from $dom on dom $count\n";
      my ($domup) = $uptime;
      if ($count > 0 ) {
         ($domup) = ($dom =~ m/{up_time\s([\d\.]+)}/)
            or die "couldn't extract up_time from $dom on dom $count\n";
      }
      my $domname = "dom-$count";
      {
         my ($tmp) = ($dom =~ m/{name\s(.+)}/);
         $domname = $tmp if ($tmp);
      }

      if ($loop <= 1) {
         $buf .= sprintf "%10s %5.2f%% cpu usage  %.2f sec over %.2f days\n",
            $domname, 100 * $domcpu/$domup, $domcpu, $domup/24/3600;
      } else {
         my $cpu = $domcpu-$lastcpu{$count};
         $totcpu += $cpu;
         $buf .= sprintf "%3d ",
            100 * $cpu/$interval;
      }
      $lastcpu{$count} = $domcpu;
      $dat = $rest;
      $count++;
      die "count exceeded" if ($count > 100);
   }
   my $period = ($datatimestamp - $lasttimestamp);
   if ($loop > 1) {  # add on idle cpu
      $buf .= sprintf "%3d", 100 * ($interval - $totcpu)/$period;
   }
   $lasttimestamp = $datatimestamp;
   print "$buf\n";
   exit if ($num_samples && $loop > $num_samples);
   sleep $interval;
}

