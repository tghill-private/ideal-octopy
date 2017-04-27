import csv

files = [	'GaN2010.csv',
			'GaN2011.csv'
		]

write_headers = True
with open('GaNMaster.csv', 'w') as output:
	for source in files:
		with open(source, 'r') as data:
			headers = data.readline()
			if write_headers:
				output.write(headers)
				write_headers = False
			output.write(''.join(data.readlines()))
print 'Done'
			