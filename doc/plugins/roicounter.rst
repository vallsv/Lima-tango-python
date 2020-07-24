RoiCounter
==========

The Region-of-Interest to Counter operation is very useful to provide online statistics on some detector areas. The operation will calculate for each image acquired the **average**, the **standard deviation**, the **sum**, the **minimum** and the **maximum pixel** values.

The Roi can be defined either with rectangle coordinates (x begin,y begin, width, height) or with arc coordinates (center x, center y, radius1, radius2, angle start, angle end). Different commands are provided for that purpose: **setRois** and **setArcRois**.

You must create first the Rois by providing unique names (**addNames** command) and then set the Roi position using the Roi index and the position (rectangle or arc position). 

The statistics can be retrieved by calling the **readCounters** command, the command returns a list of statistics per Roi and frame.

In addition to the statistics calculation one can set a mask file (**setMask** command) where null pixel will not be taken into account.

Properties
----------
This device has no property.

Attributes
----------

======================= ======= ============= ======================================================================
Attribute name		RW	Type			Description
======================= ======= ============= ======================================================================
BufferSize		rw	DevLong	      Circular buffer size in image, default is 128
CounterStatus		ro	DevLong	      Counter related to the current number of proceeded images
RunLevel		rw	DevLong	      Run level in the processing chain, from 0 to N		
State		 	ro 	State	      OFF or ON (stopped or started)
Status		 	ro	DevString     "OFF" "ON" (stopped or started)
======================= ======= ============= ======================================================================

Commands
--------

=======================	============================ ============================= ==================================================
Command name		Arg. in		             Arg. out		 	   Description
=======================	============================ ============================= ==================================================
addNames		DevVarStringArray    	     DevVarStringArray	 	   Set the names and return the corresponding indexes		
			list of Roi names    	     list of Roi indexes	
clearAllRois		DevVoid	    	     	     DevVoid			   Remove the Rois 
getNames		DevVoid		     	     DevVarStringArray	 	   Return the list of Roi names
getRoiModes		DevVarStringArray    	     DevVarStringArray	 	   Return the Roi modes 
getRois			DevVarStringArray    	     DevVarStringArray	 	   Return the Roi positions
			list of Roi names    	     list of Roi position
			     	    	     	     (roi_id,x,y,width,heigth,...)
getArcRois		DevVarStringArray    	     DevVarStringArray	 	   Return the ArcRoi positions
			list of ArcRoi names    	list of ArcRoi position
			     	    	     	     (roi_id,x,y,width,heigth,...)
Init			DevVoid		     	     DevVoid			   Do not use
readCounters		DevVarLongArray	     	     DevVarLongArray		 
removeRois		roi_id,first image   	     spectrum stack		   Return the stack of spectrum from the specified 
				     	   		 		   	   image index until the last image acquired
setArcRois		DevVarDoublArray     	     DevVoid		   	   Set the Arc Rois
			(roi_id0,centerx,centery,
			radius1,raduis2,start_angle,
			end_angle,roi_id1,...)
setMaskFile		DevVarStringArray	     DevVoid			   Set the mask file
			full path file
setRois			DevArLongArray		     DevVoid			   Set roi positions
			(roi_id0,x,y,w,h,roi_id1..)
Start			DevVoid			     DevVoid			   Start the operation on image
State			DevVoid		     	     DevLong		    	   Return the device state
Status			DevVoid		     	     DevString			   Return the device state as a string
Stop			DevVoid		     	     DevVoid			   Stop the operation on image
=======================	============================ ============================= ==================================================
