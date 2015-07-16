#!/usr/bin/env ruby

names = `ip -s -o link show`.map { |l| l.split[1] }

#for name in names
#  print name [4..-2].inspect if name ['tap-'] #name [0,4] == 'tap-'
#end

taps = names.delete_if { |name| !name ['tap-'] }  #.map { |tap| tap[4..-2] }
#puts taps.inspect

excluded = taps.map { |tap| tap[4..-2].to_i }
#puts excluded.inspect

excluded += [201,202,203,204,240]
# 201-2 tgfw 203 dh 204 vm testing 240 epoch

ips = (131..254).to_a - excluded
#ips = (131..200).to_a - excluded
#print ips.inspect

puts 'bringing up pingable alias IPs'
for i in ips
  print `echo ifconfig br0:#{i} 216.218.243.#{i} netmask 255.255.255.255`
  print `ifconfig br0:#{i} 216.218.243.#{i} netmask 255.255.255.255`
end

puts 'ensuring tap ips are not in the aliases'
for i in excluded
  print `echo ifconfig br0:#{i} down`
  print `ifconfig br0:#{i} down`
end

puts "Now restoring the tap interfaces to the bridge"
for tap in taps
  print `echo brctl addif br0 #{tap}`
  print `brctl addif br0 #{tap}`
end

