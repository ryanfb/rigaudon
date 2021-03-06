# -*- mode: python; indent-tabs-mode: nil; tab-width: 3 -*-
# vim: set tabstop=3 shiftwidth=3 expandtab:

# Copyright (C) 2010-2011 Christian Brandt
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.


from gamera.core import *    
from gamera.plugins.pagesegmentation import textline_reading_order
from gamera.toolkits.ocr.ocr_toolkit import *
from gamera.toolkits.ocr.classes import Textline,Page,ClassifyCCs
import gamera.kdtree as kdtree
import unicodedata
import sys

class SinglePage(Page):      
   def lines_to_chars(self):
      #import pprint 
      #print "inside linestochars"
      #pp = pprint.PrettyPrinter(indent=4, depth=4)
      #print "cc_lines:"
      #print pp.pprint(self.ccs_lines)
      subccs = self.img.sub_cc_analysis(self.ccs_lines)
      #print "subccs:"
      #print pp.pprint(subccs) 
      for i,segment in enumerate(self.ccs_lines):
         self.textlines.append(SingleTextline(segment, subccs[1][i]))
      #print "textlines"
      #pp.pprint(self.textlines)
      
   # Implement a simple vertical ordering
   def order_lines(self):
      self.ccs_lines.sort(lambda s,t: s.offset_y - t.offset_y)
   def page_to_lines(self):
      self.ccs_lines = self.img.bbox_mcmillan(None,1,0.5,10,5)
   #don't allow the built-in chars_to_words to add more spaces
   def chars_to_words(self):
      print "doing my chars_to_words ln 50 singlediacr"
      for textline in self.textlines:
         wordlist=[]
         word=[]
         glyphs = []
         for g in textline.glyphs:
            if textline.is_combining_glyph(g) or textline.is_small_glyph(g):
               continue
            glyphs.append(g)
         spacelist = []
         total_space = 0
         for i in range(len(glyphs) - 1):
            #print "between ", glyphs[i].id_name, " and ", glyphs[i+1].id_name, (glyphs[i + 1].ul_x - glyphs[i].lr_x)
            spacelist.append(glyphs[i + 1].ul_x - glyphs[i].lr_x)
         if(len(spacelist) > 0):
            threshold = median(spacelist)
            #print "threshold: ", threshold
            threshold = threshold * 2.7#Meineke, Kaibel: 3
         else:
            threshold  = 0
         #end calculating threshold for word-spacing
         previousNonCombining = None
         currentNonCombining = None
         for i in range(len(textline.printing_glyphs)):
               if not textline.is_combining_glyph(textline.printing_glyphs[i]): 
                 previousNonCombining = currentNonCombining
   ##              print "PNC now: ",
   ##              if previousNonCombining:
   ##                print previousNonCombining.id_name
   ##              else:
   ##                print "NONE"
                 currentNonCombining = textline.printing_glyphs[i]
   ##              print "CNC now: ", currentNonCombining.id_name
                 if(previousNonCombining and currentNonCombining and ((currentNonCombining.ul_x - previousNonCombining.lr_x) > threshold)):
   ##                  print "space: ", previousNonCombining.id_name, " and ", currentNonCombining.id_name, " : ", (currentNonCombining.ul_x - previousNonCombining.lr_x), " over ", threshold
                     cnc_dist = abs(currentNonCombining.center_x - word[-1].center_x)
                     pnc_dist = abs(previousNonCombining.center_x - word[-1].center_x)
                     #sometimes the initial smooth breathing hangs over its initial vowel, putting it before that vowel in order
                    #this is a poor attempt to make sure it doesn't get glommed onto the previous word. A positional analysis would be much better TODO
                     if ( ('combining.comma.above' in word[-1].get_main_id() or 'combining.reversed.comma.above' in word[-1].get_main_id()) and cnc_dist < pnc_dist) :# ['combining.comma.above.and.combining.acute.accent.above','combining.comma.above', 'combining.reversed.comma.above'] and cnc_dist < pnc_dist):# and not (previousNonCombining.get_main_id() in (greek_small_vowels + ['greek.small.letter.rho'] + greek_capital_vowels)):
   ##                     print "word[-1] is ", word[-1].get_main_id(), " with cl ", word[-1].center_x 
   ##                     print "cnc is ", currentNonCombining.get_main_id(), " with cl ", currentNonCombining.center_x
   ##                     print "pnc is ", previousNonCombining.get_main_id(), "with cl ", previousNonCombining.center_x
    #print "I'm worried about ", word[-1].get_main_id(), "being put with", previousNonCombining.get_main_id()
                        wordlist.append(word[:-1])
                        word = [word[-1]]
                     else:
                        wordlist.append(word)
                        word = []
               word.append(textline.printing_glyphs[i])
         if(len(word) > 0):
            wordlist.append(word)
         textline.words= wordlist

      
class ImageSegmentationError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
               
class FindAppCritTeubner(SinglePage):
	def page_to_lines(self):
		#this subdivides app. crit. in teubners
		
		#this cuts up app. crit into lines
		#self.ccs_lines = self.img.projection_cutting(Tx=25, Ty=8, noise=3)	
		#self.ccs_lines = self.img.projection_cutting(Tx=2000, Ty=5, noise=15)
		self.ccs_lines = self.img.bbox_merging(Ey=8)#this finds app. crit
		
		#word-by-word body of teubner
		#self.ccs_lines = self.img.bbox_merging(Ex=15,Ey=5)
		#self.ccs_lines = self.img.bbox_mcmillan(None,1,1,20,5)

class AppCritTeubner(SinglePage):
	def page_to_lines(self):
		#this cuts up app. crit into lines
		self.ccs_lines = self.img.projection_cutting(Tx=1700, Ty=2, noise=60)
	   #self.ccs_lines = self.img.bbox_mcmillan(None,1,.2,10,5)
	   #self.ccs_lines = self.img.bbox_merging(Ex=2,Ey=.5)
	   
class BodyTeubner(SinglePage):
	def page_to_lines(self):
		#word-by-word body of teubner
		#self.ccs_lines = self.img.bbox_merging(Ex=30,Ey=2)               
      self.ccs_lines = self.img.bbox_mcmillan(None,1,.5,10,5)
      #self.ccs_lines = self.img.bbox_merging(Ex=10,Ey=4)#finds boxes for each word

class Character(object):
   def __init__(self, glyph):
      self.maincharacter = glyph
      self.unicodename = glyph.get_main_id()
      self.unicodename = self.unicodename.replace(".", " ").upper()
      #print self.unicodename
      #self.unicodename = 
      self.combinedwith = []
      #print self.maincharacter
      
   def addCombiningDiacritics(self, diacrit):
      self.combinedwith.append(diacrit)
      pass
   
   def toUnicodeString(self):
      try:
         str = u""
         mainids = self.maincharacter.get_main_id().split(".and.")
         for char in mainids:
            if char == "skip" or char == "unclassified":
               continue
            str = str + u"%c" % return_char(char)
               
         #str = u"" + return_char(self.unicodename)
         for char in self.combinedwith:
            #char = char.get_main_id().replace(".", " ").upper()
            mainids = char.get_main_id().split(".and.")
            #print mainids
            for char in mainids:
               if char == "skip":
                  continue
               #print "added %s to output" % char
               str = str + u"%c" % return_char(char)
      
         return unicodedata.normalize('NFD', str)
      except:
         #print self.unicodename
         return u"E"
         
      
      
class SingleTextline(Textline):
   def check_capital_letter(self,glyph, height_limit, lc_form, uc_form):
      if float(glyph.height) < height_limit:
         glyph.classify_automatic(lc_form)
      else:
         glyph.classify_automatic(uc_form)
   
   def check_greek_capital_letter(self,glyph, height_limit, name):
      self.check_capital_letter(glyph, height_limit, "greek.small.letter." + name, "greek.capital.letter." + name)
      
                  #print "\treclassified capital as small one with height: ", g.height
               #else:
                  #print "\tkept one capital with height: ", g.height
   def double_check_capital_omicrons(self):
      lc_letters_of_half_height = ['greek.small.letter.alpha','greek.small.letter.nu','greek.small.letter.upsilon','greek.small.letter.sigma','greek.small.letter.omega']
      #find the average height of all the above letters as they appear in this line
      count = 0
      running_total = 0
      for g in self.glyphs:
          if g.get_main_id() in lc_letters_of_half_height: 
             running_total += g.height
             count += 1
      if count > 0:	
         #judge all the lc omicrons against this height, if it is too different, then assign it uc 
         average_height_of_letters = float(running_total) / float(count)
         #print "average height: ", average_height_of_letters
         height_limit_for_lc_omicron = average_height_of_letters + float(self.bbox.height)/float(10)
         #print "height limit: ", height_limit_for_lc_omicron
         letters_to_check = ["omicron","tau","iota"]
         for g in self.glyphs:
            g_name = g.get_main_id()
            for letter_to_check in letters_to_check:
               if g_name.endswith(letter_to_check):
                  self.check_greek_capital_letter(g,height_limit_for_lc_omicron,letter_to_check)
                  break
            if g_name in ['greek.capital.lunate.sigma.symbol','greek.lunate.sigma.symbol']:
               self.check_capital_letter(g,height_limit_for_lc_omicron,'greek.lunate.sigma.symbol','greek.capital.lunate.sigma.symbol')

   def identify_ambiguous_glyphs(self, delete_macron_below=True, check_for_underdots=True):
      if delete_macron_below:
         glyphs_copy = self.glyphs[:]
         i = 0
         while i < len(glyphs_copy):
           g = glyphs_copy[i]
           if g.get_main_id() in ["hyphen-minus","em.dash"]:
              j = 0
              while j < len(glyphs_copy):
                 if (glyphs_copy[j] != g and g.center.x > glyphs_copy[j].ul_x and g.center.x < glyphs_copy[j].lr_x) and (g.center.y > glyphs_copy[j].center.y) and "letter" in glyphs_copy[j].get_main_id():
                    del glyphs_copy[i] 
                    i = j
                    break
                 j += 1
           i += 1
         self.glyphs = glyphs_copy

      for g in self.glyphs:
         mainid = g.get_main_id()
         if mainid == "comma" or mainid == "combining.comma.above":
            #print "%s - center_y: %d - med_center: %d" % (mainid, glyph.center.y, med_center)
            if g.center.y > self.bbox.center.y:
               g.classify_automatic("comma")
            else:
               g.classify_automatic("combining.comma.above")
         elif mainid == "apostrophe":
            if g.center.y > self.bbox.center.y:
               g.classify_automatic("comma")
         elif mainid == "full.stop" or mainid == "middle.dot":
            if g.center.y > self.bbox.center.y:
               g.classify_automatic("full.stop")
               if check_for_underdots:
                  #print "checking for underdots on something with x: ", g.center.x, " and Y: ", g.center.y
                  for other in self.glyphs:
                     #print "\tother is: ", other.get_main_id(), "with center_x ", other.center.x, " center_y: ", other.center.y
                     if (g.center.x > other.ul_x and g.center.x < other.lr_x) and (g.center.y > other.center.y) and "letter" in other.get_main_id():
                        #print "classifying as dot below"
                        g.classify_automatic("combining.dot.below")
                        break
            else:
               g.classify_automatic("middle.dot")
         elif mainid == "combining.greek.ypogegrammeni":
            if g.center.y < self.bbox.center.y:
               g.classify_automatic("combining.acute.accent")
         elif mainid == "combining.acute.accent":
            if g.center.y > self.bbox.center.y:
               g.classify_automatic("combining.greek.ypogegrammeni")
         elif mainid == "right.single.quotation.mark":
            if g.center.y > self.bbox.center.y:
               #too low to be a quotation mark, must be a comma
               g.classify_automatic("comma")
         #TODO: replace these with a common function
         if g.get_main_id() == "apostrophe" or g.get_main_id() == 'right.single.quotation.mark' or g.get_main_id() == 'combining.comma.above':
            glyph_cl_x = (g.ul_x + (g.lr_x - g.ul_x)/2)
            glyph_cl_y = (g.ul_y + (g.lr_y - g.ul_y)/2)
##            print g.get_main_id(), " at: ", glyph_cl_x, glyph_cl_y
            for other in self.glyphs:
               if True:#self.is_greek_small_letter(other):
                 # print "other candidate:", other.get_main_id()
                  other_cl_y = (other.ul_y + (other.lr_y - other.ul_y)/2)
                  #print "at ", other.ul_x, other.lr_x, other_cl_y
                  if (glyph_cl_x > other.ul_x) and (glyph_cl_x < other.lr_x) and (glyph_cl_y < other_cl_y):#there is a character inside whose width the 'apostrophe's center line lies
##                     print "there is something below:", other.id_name
                     g.classify_automatic("combining.comma.above")
                     break
            #there are no other glyphs underneith; a for's else runs with no break
            else:
##               print "nothing underneith"
               g.classify_automatic("apostrophe")#it could be a right.single.quotation.mark, however
               #we have no way of telling
         if g.get_main_id() == 'greek.small.letter.iota' or g.get_main_id() == 'combining.greek.ypogegrammeni':
            glyph_cl_x = (g.ul_x + (g.lr_x - g.ul_x)/2)
            glyph_cl_y = (g.ul_y + (g.lr_y - g.ul_y)/2)
            #print g.get_main_id(), " at: ", glyph_cl_x, glyph_cl_y
            for other in self.glyphs:
               if self.is_greek_small_letter(other):
                 # print "other candidate:", other.get_main_id()
                  other_cl_y = (other.ul_y + (other.lr_y - other.ul_y)/2)
                  #print "at ", other.ul_x, other.lr_x, other_cl_y
                  if (glyph_cl_x > other.ul_x) and (glyph_cl_x < other.lr_x) and (glyph_cl_y > other_cl_y):#there is a character inside whose width the 'iota's center line lies
             #        print "there is something above:", other.id_name
                     g.classify_automatic("combining.greek.ypogegrammeni")
                     break
            #there are no other glyphs underneith; a for's else runs with no break
            else:
              # print "nothing underneith"
               g.classify_automatic("greek.small.letter.iota")         
         if g.get_main_id() == 'left.single.quotation.mark' or g.get_main_id() == 'combining.reversed.comma.above':
            glyph_cl_x = (g.ul_x + (g.lr_x - g.ul_x)/2)
            glyph_cl_y = (g.ul_y + (g.lr_y - g.ul_y)/2)
##            print g.get_main_id(), " at: ", glyph_cl_x, glyph_cl_y
            for other in self.glyphs:
		#TODO: sometimes the classifier considers an omicron to be a 'o'. In which case,
		#this algorithm will force the breathing to be a quotation mark. 
		#perhaps we shouldn't test for greek-letterness, and let the chips fall.
		#Similarly, a capital omicron also gets its breathing forced to quotation mark.
               if True: #self.is_greek_small_letter(other):
                 # print "other candidate:", other.get_main_id()
                  other_cl_y = (other.ul_y + (other.lr_y - other.ul_y)/2)
                  #print "at ", other.ul_x, other.lr_x, other_cl_y
                  if (glyph_cl_x > other.ul_x) and (glyph_cl_x < other.lr_x) and (glyph_cl_y < other_cl_y):#there is a character inside whose width the 'apostrophe's center line lies
##                     print "there is something below:", other.id_name
                     g.classify_automatic("combining.reversed.comma.above")
                     break
            #there are no other glyphs underneith; a for's else runs with no break
            else:
##               print "nothing underneith"
               g.classify_automatic("left.single.quotation.mark")
         #if a hypen-minus has something below it, it is  in fact a circumflex. Refine so that the 'something' has to be a vowel.
         if g.get_main_id() in ['left.parenthesis','greek.capital.lunate.sigma.symbol','greek.lunate.sigma.symbol']:
            for other in self.glyphs:
              if g.center_x > other.ul_x and g.center_x < other.lr_x and g.center_y < other.center_y:
                g.classify_automatic("combining.reversed.comma.above")
         if (g.get_main_id() == 'hyphen-minus') or (g.get_main_id() == 'combining.greek.perispomeni'):
            glyph_cl_x = (g.ul_x + (g.lr_x - g.ul_x)/2)
            glyph_cl_y = (g.ul_y + (g.lr_y - g.ul_y)/2)
##            print g.get_main_id(), " at: ", glyph_cl_x, glyph_cl_y
            for other in self.glyphs:
               if self.is_greek_small_letter(other):
                 # print "other candidate:", other.get_main_id()
                  other_cl_y = (other.ul_y + (other.lr_y - other.ul_y)/2)
                  #print "at ", other.ul_x, other.lr_x, other_cl_y
                  if (glyph_cl_x > other.ul_x) and (glyph_cl_x < other.lr_x) and (glyph_cl_y < other_cl_y):#there is a character inside whose width the 'apostrophe's center line lies
##                     print "there is something below:", other.id_name
                     g.classify_automatic("combining.greek.perispomeni")
                     break
            else:
               g.classify_automatic("hyphen-minus")
         greek_small_vowels = ['greek.small.letter.alpha','greek.small.letter.epsilon','greek.small.letter.eta','greek.small.letter.iota','greek.small.letter.omicron','greek.small.letter.upsilon','greek.small.letter.omega']  
         #if a middle.dot has something below it, it is  in fact a smooth breathing. Refine so that the 'something' has to be a vowel.
         if g.get_main_id() == 'middle.dot':
            glyph_cl_x = (g.ul_x + (g.lr_x - g.ul_x)/2)
            glyph_cl_y = (g.ul_y + (g.lr_y - g.ul_y)/2)
##            print g.get_main_id(), " at: ", glyph_cl_x, glyph_cl_y
            other_count = 0
            for other in self.glyphs:
               #print "other candidate:", other.get_main_id()
               other_cl_y = (other.ul_y + (other.lr_y - other.ul_y)/2)
               #print "at ", other.ul_x, other.lr_x, other_cl_y
               if (glyph_cl_x > other.ul_x) and (glyph_cl_x < other.lr_x) and (glyph_cl_y < other_cl_y):#there is a character inside whose width the 'apostrophe's center line lies
##                  print "there is something below:", other.id_name
                  if other.get_main_id() in greek_small_vowels:
                     g.classify_automatic("combining.comma.above")
                  elif other.get_main_id() == 'comma':
                     g.classify_automatic('semicolon')
                     print self.glyphs[other_count].get_main_id()
                     #TODO not sure how to delete the comma. So for now I'll leave it in place and remove in regex.
                     #del self.glyphs[other_count]
                  elif other.get_main_id() == 'full.stop':
                     g.classify_automatic('colon')
                  break
               other_count = other_count + 1

   def chars_to_words(self, lines=None):
      print "Running my dummy chars_to_words"
      
   
   def sort_glyphs(self):
      greek_capital_vowels = ['greek.capital.letter.alpha','greek.capital.letter.epsilon','greek.capital.letter.eta','greek.capital.letter.iota','greek.capital.letter.omicron','greek.capital.letter.upsilon','greek.capital.letter.omega']  
      greek_capital_rho=['greek.capital.letter.rho']
      greek_small_vowels = ['greek.small.letter.alpha','greek.small.letter.epsilon','greek.small.letter.eta','greek.small.letter.iota','greek.small.letter.omicron','greek.small.letter.upsilon','greek.small.letter.omega']  

      self.glyphs.sort(lambda x,y: cmp(x.ul_x, y.ul_x))
      self.double_check_capital_omicrons()
      self.identify_ambiguous_glyphs()
      #begin calculating threshold for word-spacing
      glyphs = []
      self.printing_glyphs = []
      for g in self.glyphs:
         # print g.id_name, g.ul_x, self.is_small_glyph(g)
         if self.is_combining_glyph(g) or self.is_small_glyph(g):
            continue
         # print g.id_name, g.ul_x
         glyphs.append(g)
      for g in self.glyphs:
         # print g.id_name, g.ul_x, self.is_small_glyph(g)
         if self.is_skip(g):
            continue
         # print g.id_name, g.ul_x
         self.printing_glyphs.append(g)  
      #scan for breathing + (accent) + capital letter
      glyphs_out = []
      reordered_glyphs = []
      just_reordered = False
##      print "printing glyphs before cap. reordering:"
     
      for glyph in self.printing_glyphs:
#         if self.is_greek_capital_letter(glyph) and len(glyphs_out):
#            print "Cap:" 
#            print glyph.id_name
#            print glyphs_out[-1].id_name
         
         can_combine_with_rough_breathing = greek_capital_vowels + greek_capital_rho
         #if just_reordered == False and len(glyphs_out) > 0 and self.is_greek_capital_letter(glyph) and self.is_combining_glyph(glyphs_out[-1]):#and the previous accent isn't too far away...
         if just_reordered == False and len(glyphs_out) > 0  and self.is_combining_glyph(glyphs_out[-1]) and (glyph.get_main_id() in can_combine_with_rough_breathing) and not (glyph.get_main_id() in greek_capital_rho and not (glyphs_out[-1] == 'combining.reversed.comma.above')):#and the previous accent isn't too far away...
         
##            print "Reorder cap?"
            capital_char_width = (glyph.lr_x - glyph.ul_x)
            if self.is_combining_glyph(glyphs_out[-1]):#if the 'combining glyph' already on the stack is actually two-in-one, then we need to
                                                       #give a bit more room.
               max_distance = capital_char_width
            else:
               max_distance = capital_char_width / 2
##            print "width: ", capital_char_width
            distance_to_accent = (glyph.ul_x - glyphs_out[-1].ul_x)
##            print "between ", glyph.id_name, " and ", glyphs_out[-1].id_name, distance_to_accent
            reordered_glyphs = []
            reordered_glyphs.append(glyph)
            if distance_to_accent < max_distance:
               just_reordered = True
               reordered_glyphs.append(glyphs_out[-1])
               glyphs_out = glyphs_out[:-1] #strip the last glyph off of this stack
##               print "reordered " + glyph.get_main_id()
               if len(glyphs_out) > 0 and self.is_combining_glyph(glyphs_out[-1]):#and it isn't too far away
                  distance_to_accent = (glyph.ul_x - glyphs_out[-1].ul_x)
##                  print "possibly two accents"
##                  print "between ", glyph.id_name, " and ", glyphs_out[-1].id_name, distance_to_accent
                  if distance_to_accent < max_distance:
                     reordered_glyphs.append(glyphs_out[-1])
                     glyphs_out = glyphs_out[:-1]
            glyphs_out = glyphs_out + reordered_glyphs
         else:
            glyphs_out.append(glyph)
            just_reordered = False
      self.printing_glyphs = glyphs_out
##      print "printing glyphs after cap. reordering:"
##      for glyph in printing_glyphs:
##         print glyph.get_main_id()




   def is_greek_capital_letter(self, glyph):
      return (glyph.get_main_id().find("greek") != -1) and (glyph.get_main_id().find("capital") != -1) and (glyph.get_main_id().find("letter") != -1)
   def is_greek_small_letter(self, glyph):
      return (glyph.get_main_id().find("greek") != -1) and (glyph.get_main_id().find("small") != -1) and (glyph.get_main_id().find("letter") != -1)   
   def is_combining_glyph(self, glyph):
      #must both have word 'combining', and not have word 'letter'
      # the latter to avoid grouped things, like 
      #greek.small.letter.eta.and.combining.acute.accent
      #which could get treated as combining, alas, forcing a
      #space on the output
      ret =  (glyph.get_main_id().find("combining") != -1) and (glyph.get_main_id().find("letter") == -1)
      return ret
   def is_joined_glyph(self, glyph):
      ret = glyph.get_main_id().find(".and.") != -1
      return ret
   def includes_letter(self,glyph):
      ret = glyph.get_main_id().find("letter") != -1
      return ret
   def is_skip(self, glyph):
      ret = glyph.get_main_id().find("skip") != -1
      return ret
   def is_small_glyph(self, glyph): 
      myId = glyph.get_main_id()
      for string in ["skip","SKIP","comma","middle.dot","apostrophe","full.stop","_split"]:
         if myId.find(string) > -1: 
            return 1
      return 0

   def to_word_tuples(self):
      k = 3
      max_k = 10
      output = []
      for word in self.words:
         med_center = median([g.center.y for g in word])
         glyphs_combining = []
         characters = []
         nodes_normal = []
         skipids = ["manual.xi.upper", "manual.xi.lower", "manual.theta.outer", "_split.splitx", "skip"]
         for glyph in word:
            mainid = glyph.get_main_id()
            
            if skipids.count(mainid) > 0:
               continue
            elif mainid == "manual.xi.middle":
               glyph.classify_automatic("greek.capital.letter.xi")
            elif mainid == "manual.theta.inner":
               glyph.classify_automatic("greek.capital.letter.theta")
            elif mainid.find("manual") != -1 or mainid.find("split") != -1:
               continue
            
            if self.is_combining_glyph(glyph) and not(self.is_joined_glyph(glyph) and self.includes_letter(glyph)):# avoid corner case where we have a glyph that is 'greek.small.letter.eta.and.combining.acute'
               glyphs_combining.append(glyph)
            else:
               c = Character(glyph)
               characters.append(c)
               #print c
               nodes_normal.append(kdtree.KdNode((glyph.center.x, glyph.center.y), c))
         
         if (nodes_normal == None or len(nodes_normal) == 0):
            continue
            
         tree = kdtree.KdTree(nodes_normal)
         
         for g in glyphs_combining:
            fast = True
            if fast:
               knn = tree.k_nearest_neighbors((g.center.x, g.center.y), k)
##               print
##               print "KNN!"
               for aKnn in knn:
##                  print aKnn.data.unicodename
                  #It isn't just whose center is closer, but also, who is below
                  if (aKnn.data.maincharacter.ul_x < g.center.x) and (aKnn.data.maincharacter.lr_x > g.center.x):
                     aKnn.data.addCombiningDiacritics(g)
##                     print "this is determined to be below"
                     break
               else:
                  search_x_point = 0
                  if (g.get_main_id() == 'combining.grave.accent'):
                     search_x_point = g.lr_x
                  elif (g.get_main_id() == 'combining.acute.accent'):
                     search_x_point = g.ul_x
                  else:
##                     print "I give up: no NN below??"
                     knn[0].data.addCombiningDiacritics(g)
                     break
                  for aKnn in knn:
                     if (aKnn.data.maincharacter.ul_x < search_x_point) and (aKnn.data.maincharacter.lr_x > search_x_point):
                        aKnn.data.addCombiningDiacritics(g)
##                        print "found on edge of", aKnn.data.unicodename
                        break
            else:
               found = False
               while (not found) and k < max_k:
                  knn = tree.k_nearest_neighbors((g.center.x, g.center.y), k)
                  
                  for nn in knn:
                     if (nn.data.maincharacter.get_main_id().split(".").count("greek") > 0) and not found:
                        nn.data.addCombiningDiacritics(g)
                        found = True
                        break
               
                  k = k + 2      
                  
         wordString = ""      
         for c in characters:
            #output = output + c.toUnicodeString()
            wordString = wordString + c.toUnicodeString()
         #output = output + wordString + " "
         output.append((wordString,word))
      return output

   def to_string(self):
     
      tuples = self.to_word_tuples()
      stringOut = ""
      x = 0
      for t in tuples:
         stringOut = stringOut + t[0] + " "

        # print foo, bar

      return stringOut  


   

