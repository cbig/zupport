# Import modules
import arcpy
import sys
import traceback

# Set local variables
indata = arcpy.GetParameterAsText()

try:
	# check if indata is in StatePlane, has no PRJ, or one other than StatePlane
	if arcpy.Exists(indata):
		arcpy.SetParameterAsText(1,"true") #The first parameter refers to the "Yes" variable
		arcpy.SetParameterAsText(2,"false") #The second parameter refers to the "No" variable
		arcpy.AddMessage("File %s exists" % indata) 

	else:
		arcpy.SetParameterAsText(1,"false") #The first parameter refers to the "Yes" variable
		arcpy.SetParameterAsText(2,"true") #The second parameter refers to the "No" variable
		arcpy.AddMessage("File % does not exist" % indata) 

except: 
	tb = sys.exc_info()[2]
	tbinfo = traceback.format_tb(tb)[0] 
	pymsg = tbinfo + "\n" + str(sys.exc_type) 
	arcpy.AddError("Python Messages: " + pymsg + " GP Messages: " + arcpy.GetMessages(2)) 
