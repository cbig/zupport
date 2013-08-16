# Import modules
import arcpy
import sys
import traceback

# Set local variables
prj = "" 
indata = arcpy.GetParameterAsText()
row_count = arcpy.GetCount_management(indata)

try:
	# check if indata is in StatePlane, has no PRJ, or one other than StatePlane
	if row_count > 0:
		arcpy.SetParameterAsText(1,"true") #The first parameter refers to the "HasSomething" variable
		arcpy.SetParameterAsText(2,"false") #The second parameter refers to the "HasNothing" variable
		arcpy.AddMessage("Selection has rows") 

	else:
		arcpy.SetParameterAsText(1,"false") #The first parameter refers to the "HasSomething" variable
		arcpy.SetParameterAsText(2,"true") #The second parameter refers to the "HasNothing" variable
		arcpy.AddMessage("Selection has no rows") 

except: 
	tb = sys.exc_info()[2]
	tbinfo = traceback.format_tb(tb)[0] 
	pymsg = tbinfo + "\n" + str(sys.exc_type) 
	arcpy.AddError("Python Messages: " + pymsg + " GP Messages: " + arcpy.GetMessages(2)) 
