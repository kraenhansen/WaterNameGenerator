import logging
import sys
import json
import operator
import Queue

'''
These are the steps to follow:
1) Generate a language analysis file, this is used as
    a basis for what combinations of letters are
    pronouncable and which are not.
2) Generate a wordlist of pronouncable names.
3) Check the advailability of each of the names and
    compute interesting statistics on the names ie.
    number of results when searching on google, etc.
4) Compute the best name from the list of advailable.
'''

#FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
FORMAT = '%(levelname)-5s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('waternamegen')

from optparse import OptionParser

alphabeth = "abcdefghijklmnopqrstuvwxyz"

def generateLanguage(plaintext, output_file = None):
	log.info("Generating the language file: %u charecters long.", len(plaintext))

	letter_frequencies = dict()
	digraph_frequencies = dict()
	trigraph_frequencies = dict()

	letter_count = 0
	digraph_count = 0
	trigraph_count = 0

	current_letter = None
	last_letter = None
	second_last_letter = None
	for i in range(0, len(plaintext)):
		current_letter = plaintext[i]
		if current_letter in alphabeth:
			letter_count += 1
			if current_letter in letter_frequencies.keys():
				letter_frequencies[current_letter] += 1
			else:
				letter_frequencies[current_letter] = 1
			# Check for digraph
			if last_letter != None and last_letter in alphabeth: # We have a digraph!
				digraph = last_letter + current_letter
				digraph_count += 1
				if digraph in digraph_frequencies.keys():
					digraph_frequencies[digraph] += 1
				else:
					digraph_frequencies[digraph] = 1
				# Check for trigraph
				if second_last_letter != None and second_last_letter in alphabeth: # We have a trigraph!
					trigraph = second_last_letter + digraph
					trigraph_count += 1
					if trigraph in trigraph_frequencies.keys():
						trigraph_frequencies[trigraph] += 1
					else:
						trigraph_frequencies[trigraph] = 1
		# Updating last letters
		second_last_letter = last_letter
		last_letter = current_letter

	# Output
	if output_file == None:

		letter_frequencies_sorted = sorted(letter_frequencies.iteritems(), key=operator.itemgetter(1))
		letter_frequencies_sorted.reverse()
		print "Letter frequencies:"
		for (letter, frequency) in letter_frequencies_sorted:
			print "\t{:}:{:7,.2%} = {:} occurances".format(letter, float(frequency) / letter_count, frequency)

		digraph_frequencies_sorted = sorted(digraph_frequencies.iteritems(), key=operator.itemgetter(1))
		digraph_frequencies_sorted.reverse()
		print "Digraph frequencies:"
		for (digraph, frequency) in digraph_frequencies_sorted:
			print "\t{:}:{:7,.2%} = {:} occurances".format(digraph, float(frequency) / digraph_count, frequency)


		trigraph_frequencies_sorted = sorted(trigraph_frequencies.iteritems(), key=operator.itemgetter(1))
		trigraph_frequencies_sorted.reverse()
		print "Trigraph frequencies:"
		for (trigraph, frequency) in trigraph_frequencies_sorted:
			print "\t{:}:{:7,.2%} = {:} occurances".format(trigraph, float(frequency) / trigraph_count, frequency)
		
	else:
		# Normalize
		for letter in letter_frequencies.keys():
			letter_frequencies[letter] = float(letter_frequencies[letter]) / letter_count
		for digraph in digraph_frequencies.keys():
			digraph_frequencies[digraph] = float(digraph_frequencies[digraph]) / digraph_count
		for trigraph in trigraph_frequencies.keys():
			trigraph_frequencies[trigraph] = float(trigraph_frequencies[trigraph]) / trigraph_count

		output = open(output_file, 'w')
		json.dump(dict(
			letter_frequencies = letter_frequencies,
			digraph_frequencies = digraph_frequencies,
			trigraph_frequencies = trigraph_frequencies
		), output)
		output.close()

def adjacentNames(name, letters, digraphs, trigraphs):
	result = []
	if len(name) == 0:
		letters = letters
	elif len(name) == 1:
		#print "Case 1:",name
		letters = []
		last_letter = name[-1:]
		#print "last_letter:",last_letter
		for digraph in digraphs:
			if digraph[0][:1] == last_letter:
				letters.append(digraph[0][-1:])
	else:
		letters = []
		last_digraph = name[-2:]
		for trigraph in trigraphs:
			if trigraph[0][:2] == last_digraph:
				letters.append(trigraph[0][-1:])
	#print "Using letters: ",letters
	for l in letters:
		result.append(name+l[0])
	return result

def generateNames(language, min_length = 0, max_length = None, number_of_names = None, output_file = None, top_letters = 1.0, top_digraphs = 1.0, top_trigraphs = 1.0):
	log.info("Generating the names.")
	log.info("Minimum length: %u", min_length)
	if max_length != None:
		log.info("Maximum length: %u", max_length)
	if number_of_names != None:
		log.info("Number of names: %u", number_of_names)
	log.info("Sorting language.")

	letters = sorted(language['letter_frequencies'].iteritems(), key=operator.itemgetter(1))
	letters.reverse()
	letter_count = int(len(letters) * top_letters)
	print "Using top %u of %u letters." % (letter_count, len(letters))
	letters = letters[:letter_count] # Only considering the top half.

	digraphs = sorted(language['digraph_frequencies'].iteritems(), key=operator.itemgetter(1))
	digraphs.reverse()
	digraph_count = int(len(digraphs) * top_digraphs)
	print "Using top %u of %u digraphs." % (digraph_count, len(digraphs))
	digraphs = digraphs[:digraph_count] # Only considering the top half.

	trigraphs = sorted(language['trigraph_frequencies'].iteritems(), key=operator.itemgetter(1))
	trigraphs.reverse()
	trigraph_count = int(len(trigraphs) * top_trigraphs)
	print "Using top %u of %u trigraphs." % (trigraph_count, len(trigraphs))
	trigraphs = trigraphs[:trigraph_count] # Only considering the top half.

	# print "Letters ordered by frequency:", letters
	# print "Digraphs ordered by frequency:", digraphs
	# print "Trigraphs ordered by frequency:", trigraphs

	Q = Queue.Queue()
	# Enqueue the empty name ...
	Q.put("")
	name_count = 0
	while not Q.empty():
		name = Q.get()

		for adjacent_name in adjacentNames(name, letters, digraphs, trigraphs):
			Q.put(adjacent_name)

		if name == "":
			continue # This name is not interesting.
		elif max_length != None and len(name) > max_length:
			log.info("Name got too long ..")
			break
		elif number_of_names != None and name_count >= number_of_names:
			log.info("Done, number of names was reached.")
			break
		elif len(name) < min_length:
			continue
		else:
			print name
			name_count += 1

	'''
	name_count = 0
	name = None
	state = {}
	while number_of_names == None or name_count < number_of_names:
		name = generateNextName(name, most_frequent_single_letters, most_frequent_two_letters, state)

		if max_length != None and len(name) > max_length:
			log.info("Name became too long.")
			break

		name_count += 1
		print "%u: %s" % (name_count, name)
	'''

if __name__ == "__main__":
	print "=== You're running the Water Name Generator CLI ===\n"

	usage = "\n".join(["Usage: %prog [options] MODE FILE1 [FILE2]",
			"Where MODE is either 'language' or 'names':",
			"[language] This mode is generating a language analysis file from the",
			"	plaintext inputted as FILE1, this is printed to stdout or optionally",
			"	to FILE2",
			"[names] This mode generates names from a language analysis file",
			"	inputted as FILE1. The names are outputted to stdout or optionally",
			"	to FILE2. Use the runtime options -m or --min for the minimum length",
			"	and -M or --max for the maximum length of the names.",
			"   Optionally use -n or --number to denote the number of names to generate."])

	parser = OptionParser(usage=usage)
	parser.add_option("-v", "--verbose",
		action="store_true", dest="verbose", default=True,
		help="make lots of noise [default]")
	parser.add_option("-q", "--quiet",
		action="store_false", dest="verbose",
		help="be very quiet")
	parser.add_option("-m", "--minlen",
		type="int",
		default=0,
		help="Minimum length of a name to be generated.")
	parser.add_option("-M", "--maxlen",
		type="int",
		help="[optional] Maximum length of a name to be generated.")
	parser.add_option("-n", "--number",
		type="int",
		help="[optional] Number of names to generate, default is unlimited.")
	parser.add_option("-l", "--letters",
		type="float",
		default=1.0,
		help="[optional] Fraction of the top letters to use.")
	parser.add_option("-d", "--digraphs",
		type="float",
		default=1.0,
		help="[optional] Fraction of the top digraphs to use.")
	parser.add_option("-t", "--trigraphs",
		type="float",
		default=1.0,
		help="[optional] Fraction of the top trigraphs to use.")

	(options, args) = parser.parse_args()

	# TODO: Set logging level from verbose
	
	if len(args) == 0:
		log.error("You have to specify a MODE.")
		parser.print_help()
		sys.exit(-1)
	elif args[0].lower() == "language":
		if len(args) >= 2:
			plaintext_file = open(args[1], 'r')
			plaintext = plaintext_file.read()
			plaintext_file.close()
		else:
			log.error("No plaintext file was given af FILE1.")
			parser.print_help()
			sys.exit(-1)
		if len(args) >= 3:
			output_file = args[2]
		else:
			output_file = None
		generateLanguage(plaintext, output_file)
	elif args[0].lower() == "names":
		if len(args) >= 2:
			language_file = open(args[1], 'r')
			language = json.load(language_file)
			language_file.close()
		else:
			log.error("No language file was given af FILE1.")
			parser.print_help()
			sys.exit(-1)
		if len(args) >= 3:
			output_file = args[2]
		else:
			output_file = None
		generateNames(language,
			min_length = options.minlen,
			max_length = options.maxlen,
			number_of_names = options.number,
			output_file = output_file,
			top_letters = options.letters,
			top_digraphs = options.digraphs,
			top_trigraphs = options.trigraphs,
			)
	else:
		log.error("Unsupported MODE.")
		parser.print_help()
		sys.exit(-1)

