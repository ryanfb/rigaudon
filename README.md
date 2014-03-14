rigaudon
========

Polytonic Greek OCR engine derived from Gamera, and based on the work of Dalitz and Brandt <http://gamera.informatik.hsnr.de/addons/greekocr4gamera/index.html>

NOTES
-----

Pre-requisites:

 * FreeImage
 * Lynx
 * Java
 * Python
 * [gamera](http://gamera.informatik.hsnr.de/)
 * [gamera-ocr](http://gamera.informatik.hsnr.de/addons/ocr4gamera/)
 * greekocr4gamera: install the customized version from this repo in `./Gamera/greekocr-1.0.0`
 * [Mahotas](http://luispedro.org/software/mahotas): pip install mahotas
 * matplotlib: pip install matplotlib

Mac notes:
----------

For gamera, gamera-ocr, and greekocr4gamera I surrendered and used GCC instead of clang. So for each of these to install, I ran:

    CC=gcc-4.2 CXX=g++-4.2 python setup.py build && sudo python setup.py install

Install the `apple-gcc42` package from [Homebrew](http://brew.sh/) first.

You'll also need the `parallel` and `findutils` (for gfind) packages.

Running:
--------
Run:

    ./Scripts/Variables/pre_process_volume_from_archive.sh

Licence
-------

The work in this github repository is licenced under GPLv2. 

