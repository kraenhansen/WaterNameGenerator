WaterNameGenerator
==================

What a name generator

Try generating a language from the GNU manifesto:

`python waternamegen.py language samples/gnu-manifesto samples/gnu-manifesto.lang`

Afterwards you can generate a list of 100 names, from length 4 to 5

`python waternamegen.py -n 100 -m 4 -M 5 names samples/gnu-manifesto.lang > gnu-manifesto.names`

You can tune the parameters to use only top 10% most frequent letters, 50% most frequent digraphs and 80% most frequent trigraphs, adding

`-l 0.1 -d 0.5 -t 0.8`

A good sample of names could be generated using 

`python waternamegen.py -m 6 -M 6 -n 100 -l 0.5 -d 0.3 -t 0.1 names samples/gnu-manifesto.lang > gnu-manifesto.names`
