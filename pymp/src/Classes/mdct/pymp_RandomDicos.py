'''
#                                                                            
#                       Classes.mdct.pymp_RandomDicos                                     
#                                                                            
#                                                
#                                                                            
# M. Moussallam                             Created on Nov 12, 2012  
# -----------------------------------------------------------------------
#                                                                            
#                                                                            
#  This program is free software; you can redistribute it and/or             
#  modify it under the terms of the GNU General Public License               
#  as published by the Free Software Foundation; either version 2            
#  of the License, or (at your option) any later version.                    
#                                                                            
#  This program is distributed in the hope that it will be useful,          
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             
#  GNU General Public License for more details.                              
#                                                                            
#  You should have received a copy of the GNU General Public License         
#  along with this program; if not, write to the Free Software               
#  Foundation, Inc., 59 Temple Place - Suite 330,                            
#  Boston, MA  02111-1307, USA.                                              
#      


This file handle dctionaries that are used in Randomized Matching Pursuits
see [1] for details

[1] M. Moussallam, L. Daudet, et G. Richard, 
"Matching Pursuits with Random Sequential Subdictionaries"
Signal Processing, vol. 92, pp. 2532-2544 2012.
                                                                      
'''

from Classes.mdct.pymp_MDCTDico import pymp_MDCTDico
from Classes import pymp_Log
import pymp_MDCTAtom as Atom
import pymp_RandomBlocks as Block
import math
from numpy import  zeros , abs, sum , array , random
from xml.dom.minidom import Document 

global _Logger
_Logger = pymp_Log.pymp_Log('RandomMDCTDico', level=0)

class pymp_RandomDico(pymp_MDCTDico):
    """ in this case , the MP dictionary is shifted in time at each iteration in a pre-defined manner     
        
    """
    
    # properties
    randomType = 'none' # type of sequence , Scale , Random or Dicho
    iterationNumber = 0 # memorizes the position in the sequence
    nbSim = 1;          # number of consecutive similar position
    nature = 'RandomMDCT'
    
    # constructor
    def __init__(self , sizes=[] , randomType = 'random' , nbSame = 1 , windowType = None):
        self.randomType = randomType
        self.sizes = sizes
        self.nbSim = nbSame
        
        self.windowType = windowType;
        
    def initialize(self , residualSignal ):
        self.blocks = [];
        self.bestCurrentBlock = None;
        self.startingTouchedIndex = 0;
        self.endingTouchedIndex = -1;
        
        for mdctSize in self.sizes:
            # check whether this block should optimize time localization or not
            self.blocks.append(Block.pymp_RandomBlock(mdctSize , residualSignal ,randomType = self.randomType , nbSim = self.nbSim , windowType = self.windowType));

    def computeTouchZone(self, previousBestAtom):
        # if the current time shift is about to change: need to recompute all the scores
        if (self.nbSim > 0):
            if ( (self.iterationNumber+1) % self.nbSim == 0): 
                self.startingTouchedIndex = 0;
                self.endingTouchedIndex = -1
            else:
                self.startingTouchedIndex = previousBestAtom.timePosition - previousBestAtom.length/2;
                self.endingTouchedIndex = self.startingTouchedIndex + 1.5*previousBestAtom.length
        else:
            self.startingTouchedIndex = previousBestAtom.timePosition - previousBestAtom.length/2;
            self.endingTouchedIndex = self.startingTouchedIndex + 1.5*previousBestAtom.length
        
        
    def update(self , residualSignal , iterationNumber=0 , debug=0):
        self.maxBlockScore = 0;
        self.bestCurrentBlock = None;
        self.iterationNumber = iterationNumber
        # BUGFIX STABILITY
#        self.endingTouchedIndex = -1
#        self.startingTouchedIndex = 0
        
        for block in self.blocks:
            startingTouchedFrame = int(math.floor(self.startingTouchedIndex / (block.scale/2)))
            if self.endingTouchedIndex > 0:
                endingTouchedFrame = int(math.floor(self.endingTouchedIndex / (block.scale/2) )) + 1; # TODO check this
            else:
                endingTouchedFrame = -1;

            block.update(residualSignal , startingTouchedFrame , endingTouchedFrame ,iterationNumber )

            if abs(block.maxValue) > self.maxBlockScore:
#                self.maxBlockScore = block.getMaximum()    
                self.maxBlockScore = abs(block.maxValue)
                self.bestCurrentBlock = block;

    def getSequences(self , length):
        sequences =[]
        for block in self.blocks:
            sequences.append(block.TSsequence[0:length])
        return sequences;


class pymp_RandomSizeDico(pymp_MDCTDico):
    """ in this case , the MP dictionary is an orthonormal MDCT basis of random scale at each iteration """
    
    # properties
    randomType = 'none' # type of sequence , Scale , Random or Dicho
    iterationNumber = 0 # memorizes the position in the sequence
    nbSim = 1;          # number of consecutive similar position
    sequence = [];
    useC = True
    # constructor
    def __init__(self , sizes=[] , randomType = 'scale' , nbSame = 1 , windowType = None):
        self.randomType = randomType
        self.sizes = sizes
        self.nbSim = nbSame
        M = len(sizes);
        if self.randomType == 'scale':
            self.sequence = range(M)
        elif self.randomType == 'random':
            self.sequence = [int(math.floor(M *i)) for i in random.random(100)]
            

    def computeTouchZone(self, previousBestAtom):
        # need to recompute all the scores since the base have changed
        if (self.nbSim > 0):
            if ( (self.iterationNumber+1) % self.nbSim == 0): 
                self.startingTouchedIndex = 0;
                self.endingTouchedIndex = -1
            else:
                self.startingTouchedIndex = previousBestAtom.timePosition - previousBestAtom.length/2;
                self.endingTouchedIndex = self.startingTouchedIndex + 1.5*previousBestAtom.length
        else:
            self.startingTouchedIndex = previousBestAtom.timePosition - previousBestAtom.length/2;
            self.endingTouchedIndex = self.startingTouchedIndex + 1.5*previousBestAtom.length
        
        
    def update(self , residualSignal , iterationNumber=0 , debug=0):
        self.maxBlockScore = 0;
        self.bestCurrentBlock = None;
        self.iterationNumber = iterationNumber
        
        # selects a size at random ! # 
        sizeIdx = self.sequence[(iterationNumber / self.nbSim) % len(self.sequence)];
        block = self.blocks[sizeIdx]
        
        startingTouchedFrame = int(math.floor(self.startingTouchedIndex / (block.scale/2)))
        if self.endingTouchedIndex > 0:
            endingTouchedFrame = int(math.floor(self.endingTouchedIndex / (block.scale/2) )) + 1; # TODO check this
        else:
            endingTouchedFrame = -1;

        block.update(residualSignal , startingTouchedFrame , endingTouchedFrame )

        self.maxBlockScore = abs(block.maxValue)
        self.bestCurrentBlock = block;

    def getSequences(self , length):
        sequences =[]
        for block in self.blocks:
            sequences.append(block.TSsequence[0:length])
        return sequences;

class pymp_SubRandomDico(pymp_RandomDico):
    """ UNDER DEVELOPPMENT DO NOT USE 
    subclass with no overlapping between adjacent frames : dictionary size is reduced by two """
    
    # constructor
    def __init__(self , sizes=[] , randomType = 'scale' , nbSame = 1 , windowType = None , subsamplingFactor = 2):
        self.randomType = randomType
        self.sizes = sizes
        self.nbSim = nbSame
        
        self.windowType = windowType;
        
        self.subFactor = subsamplingFactor;
        
    
    def initialize(self , residualSignal ):
        self.blocks = [];
        self.bestCurrentBlock = None;
        self.startingTouchedIndex = 0;
        self.endingTouchedIndex = -1;
        
        for mdctSize in self.sizes:
            # Create corresponding blocks
            self.blocks.append(Block.pymp_SubRandomBlock(mdctSize , residualSignal ,
                                                               randomType = self.randomType , 
                                                               nbSim = self.nbSim , windowType = self.windowType , 
                                                               subFactor = self.subFactor));

class pymp_VarSizeRandomDico(pymp_RandomDico):
    """ UNDER DEVELOPPMENT DO NOT USE 
        subclass with varying subdictionary sizes"""
    
    # constructor
    def __init__(self , sizes=[] , randomType = 'scale' , nbSame = 1 , windowType = None , subsamplings = 1):
        self.randomType = randomType
        self.sizes = sizes
        self.nbSim = nbSame
        
        self.windowType = windowType;
        
        
        self.subFactorList = subsamplings;
        
    
    def initialize(self , residualSignal ):
        self.blocks = [];
        self.bestCurrentBlock = None;
        self.startingTouchedIndex = 0;
        self.endingTouchedIndex = -1;
        
        for mdctSize in self.sizes:
            # Create corresponding blocks
            self.blocks.append(Block.pymp_VarSizeRandomBlock(mdctSize , residualSignal ,
                                                               randomType = self.randomType , 
                                                               nbSim = self.nbSim , windowType = self.windowType , 
                                                               subFactorList = self.subFactorList));





