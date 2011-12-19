#!/usr/bin/env python
# vim: set fileencoding=utf-8:

# Generate text index for PDF files
# Copyright (C) 2011  Mark Nevill
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re, subprocess, sys, os, os.path, getopt, math

invalid = re.compile(r'\d+|^[a-z]')

def extract_pages(filename, offset, pages):
    print >>sys.stderr, ("extracting %d pages from %s starting with offset %d"
            % (pages, filename, offset))
    for x in range(1, pages+max(1, offset)):
        subprocess.Popen(["pdftotext", "-f", str(x), "-l", str(x), filename,
            "out."+str(x)+".txt"], stdout=subprocess.PIPE).wait()

def get_index(offset, pages):
    print >>sys.stderr, ("generating index for %d pages starting with offset"
            " %d" % (pages, offset))
    index = {}
    for x in range(offset, pages+offset):
        filename = "out."+str(x)+".txt"
        file = open(filename)
        text = file.read()
        file.close()
        #words = re.split(u'[^a-zA-Z0-9äöüëÄÖÜË]+', text)
        #words = re.split('\W+', text, re.UNICODE)
        words = re.split('\W+', text)
        #words = re.split(u'[ ()<>{}[\],.-\\\n\'&*!%:;_•≤½„“∫→—]+', text)
        for word in ((word for word in words if not invalid.match(word))):
            locations = index.setdefault(word, [])
            if len(locations) == 0 or locations[-1] != str(x+offset):
                locations.append(str(x+offset))
                index[word] = locations
    return index

def clear_pages(offset, pages):
    print >>sys.stderr, ("clearing %d pages starting with offset %d" % (pages,
        offset))
    for x in range(offset, pages+offset):
        os.remove("out."+str(x)+".txt")

def make_index(indices, max_page_numbers):
    if len(indices) == 1:
        megaindex = indices[0][1]
    else:
        megaindex = {}
        for prefix, index in indices:
            for word, pagenumbers in index.iteritems():
                #ret = subprocess.call(["wget", "-q", "-O/dev/null", "de.wikipedia.org/wiki/"+word])
                #print >>sys.stderr, word+": "+str(ret)
                megaindex.setdefault(word, []).extend(prefix+"-"+number for number in pagenumbers)
    for word, pagenumbers in megaindex.iteritems():
        if len(pagenumbers) < max_page_numbers:
            print word + ": " + ", ".join(pagenumbers)

def usage(exe, outstream):
    print >>outstream, main.__doc__.replace('index.py', exe)

def check_program(program):
    if subprocess.call(["which", program], stdout=subprocess.PIPE) != 0:
        print >>sys.stderr, ("the required program %s could not be found" % program)
        return False
    return True

def parse_argv(argv, default_opts=None):
    if default_opts is None:
        opts = {}
    else:
        opts = dict(default_opts)
    try:
        optlist, args = getopt.getopt(argv[1:], "hp:o:l:", ["help", "pages=",
            "offset=", "limit="])
    except getopt.GetoptError, err:
        print >>sys.stderr, "Error: "+str(err)
        usage(argv[0], sys.stderr)
        opts['exit'] = 1
        return opts
    for o, a in optlist:
        if o in ("-h", "--help"):
            usage(argv[0], sys.stdout)
            opts['exit'] = 0
            return opts
        elif o in ("-p", "--pages"):
            opts['pages'] = int(a)
        elif o in ("-o", "--offset"):
            opts['offset'] = int(a)
        elif o in ("-l", "--limit"):
            opts['limit'] = int(a)
        else:
            assert False, "unhandled option"
    if len(args) < 1:
        print >>sys.stderr, "Error: Mising input files"
        usage(argv[0], sys.stderr)
        opts['exit'] = 1
    else:
        opts['files'] = args
    return opts

def main(argv):
    """Usage:
        index.py --help
        index.py [options] <pdf-file>
        index.py [options] <pdf-files...>

    Options:
        -h
        --help
            Print usage information and exit

        -p <pages>
        --pages=<pages>
            Explicitly set total number of pages in pdf (only for single
            pdf invocation)

        -o <offset>
        --offset=<offset>
            Set page number that is actual page 1. The default is 1, i.e.
            the first page is page 1.

        -l <limit>
        --limit=<limit>
            This determines the number of entries which will result in a
            word being ignored, i.e. removed from the index. The default
            is some random function that depends on the number of files.

    With a single pdf file argument, an index of words and page numbers is
    printed to stdout. With multiple pdf, an index of words and the page
    numbers prefixed with the filename of the pdf (without extension) is
    printed. To prefix the indices with chapter numbers, rename the files
    to <chapter>.pdf before running this program.

    Note that this program generates a lot of intermediate files called
    out.<num>.txt, which are subsequently deleted.\
    """
    # parse arguments
    opts = parse_argv(argv, {'offset': 1, 'pages': None})

    # copy opts into locals
    for var in opts:
        exec ''.join([var, " = opts['", var, "']"])

    # check for dependancies
    depsfound = check_program("pdftotext")
    if pages is None or len(files) > 1:
        # if no pages are given or multiple files need to detect
        depsfound = check_program("pdfinfo") and depsfound
        pages = None

    # if arguments were invalid, exit now
    if 'exit' in opts:
        return exit

    # exit due to dependancy issues after other exit reasons so their exit
    # codes are used instead
    if not depsfound:
        print >>sys.stderr, "Error: Missing dependancies"
        return 2

    # set default limit based on number of files
    if 'limit' not in opts:
        limit = 8 + (len(files)-1)/4

    # perform the actual convertion
    indices = [];
    for file in files:
        if pages is None:
            # detect number of pages
            p = subprocess.Popen(["pdfinfo", file], stdout=subprocess.PIPE)
            p.wait()
            pout = p.communicate()[0]
            file_pages = int(re.search(r'^Pages:\s*(\d+)', str(pout), re.MULTILINE).group(1))
        else:
            file_pages = pages
        extract_pages(file, offset, file_pages)
        indices.append((os.path.splitext(os.path.basename(file))[0], get_index(offset, file_pages)))
        clear_pages(offset, file_pages)
    make_index(indices, limit)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
