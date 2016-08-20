objShell := ComObjCreate("Shell.Application") 
objFolder := objShell.Namespace(A_ScriptDir . "\") 
objFilename := objFolder.Parsename(A_ScriptName)

oDetails := Object()
Loop {
  iAttribute := objFolder.GetDetailsOf(objFolder.Items, A_Index)
  if (iValue := objFolder.GetDetailsOf(objFilename, A_Index)) ;only add attribs with values
    oDetails[iAttribute] := iValue
} Until iAttribute = ""

alphabet := Object() ;sub-object
Loop 26
  alphabet[A_Index] := Chr(64+A_Index)

alphabet_s := Object() ;sub-sub-object
Loop 26
  alphabet_s[A_Index] := Chr(96+A_Index)

alphabet.alphabet_s := alphabet_s
oDetails.alphabet := alphabet

;--- Double-click an object entry to get that objects array
array_list(oDetails)
;--- You can set options also
array_list(oDetails,"Font=s12:Arial, GuiOptions=+AlwaysOnTop -Sysmenu, GuiShowOptions=w500 h300 center")
ExitApp

#Include Array.ahk  ;uncomment if not in Lib