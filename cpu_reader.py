#!/usr/bin/env python

import os
import time
	
# See proc(5) for information about the columns in /proc/stat
STAT_COLUMNS = ['name', 'user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest-nice']
COLLECTION_INTERVAL = 3

def read_cpu_data():
	"""Read data for all cpus from /proc/stat  A dict is created for each cpu, mapping column names to values."""
	cpus = {}
	with open('/proc/stat', 'r') as stat_fd:
		for line in stat_fd:
			if not line.startswith('cpu'):
				continue
			# Create a dict mapping the cpu column names to values.
			cpu = dict(zip(STAT_COLUMNS, line.strip().split()))
			cpus[cpu['name']] = cpu
	return cpus

def diff_cpu_data(prev, cur, ticks_elapsed):
	"""Calculate the different between two sets of cpu data.A new set with updated data is returned."""
	if not prev or not cur:
		return None
	diff_cpus = {}
	for cpu_name, prev_cpu in prev.iteritems():
		# If a cpu is not included in both sets, skip it.
		if cpu_name not in cur:
			continue
                # if a cpu0 is included skip it.
                if cpu_name=='cpu0':
                    continue
		cur_cpu = cur[cpu_name]
		diff_cpu = {'name': cpu_name}
		diff_cpus[cpu_name] = diff_cpu
		for column_name in prev_cpu:
			if column_name == 'name' or column_name not in cur_cpu:
				continue
			try:
				# This calculates the amount of time spent
				# doing a cpu usage type, in percent.
				# The diff value (cur-prev) is the amount of
				# ticks spent on this task since the last
				# reading, divided by the total amount of ticks
				# elapsed.
				diff_cpu[column_name] = float(int(cur_cpu[column_name]) - int(prev_cpu[column_name])) / ticks_elapsed * 10
			except ValueError:
				pass
	return diff_cpus


def print_cpu_data(cpu_data):
	""" Prints the tsdb format values in percent. """
	ts = int(time.time())
        for cpu in cpu_data.itervalues():
		for column in STAT_COLUMNS:
			if column == 'name':
				value = cpu.get(column, 'unknown')
			else:
				value = '%.2f' % cpu.get(column, 0)
				print "proc.stat.cpu_pct %-10s %s type=%s" % (ts, value, column)
                        


def cpu_percentage():
	# The cpu columns in /proc/stat show the amount of time spent doing
	# each type, measured in units of USER_HZ (clock ticks).
	# sysconf(3) describes SC_CLK_TCK as the number of clock ticks per second.
	# Ie. this calculated how many clock ticks have elapsed between each
	# reading of /proc/stat
        ticks_elapsed = os.sysconf(os.sysconf_names['SC_CLK_TCK']) * COLLECTION_INTERVAL
	prev_cpu_data = None
	cur_cpu_data = None
	while True:
		prev_cpu_data = cur_cpu_data
		cur_cpu_data = read_cpu_data()
		cpu_data_diff = diff_cpu_data(prev_cpu_data, cur_cpu_data, ticks_elapsed)
		if cpu_data_diff:
			print_cpu_data(cpu_data_diff)
		time.sleep(COLLECTION_INTERVAL)

if __name__ == '__main__':
	cpu_percentage()
