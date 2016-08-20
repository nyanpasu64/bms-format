/*           ,---,                                          ,--,    
           ,--.' |                                        ,--.'|    
           |  |  :                      .--.         ,--, |  | :    
  .--.--.  :  :  :                    .--,`|       ,'_ /| :  : '    
 /  /    ' :  |  |,--.  ,--.--.       |  |.   .--. |  | : |  ' |    
|  :  /`./ |  :  '   | /       \      '--`_ ,'_ /| :  . | '  | |    
|  :  ;_   |  |   /' :.--.  .-. |     ,--,'||  ' | |  . . |  | :    
 \  \    `.'  :  | | | \__\/: . .     |  | '|  | ' |  | | '  : |__  
  `----.   \  |  ' | : ," .--.; |     :  | |:  | : ;  ; | |  | '.'| 
 /  /`--'  /  :  :_:,'/  /  ,.  |   __|  : ''  :  `--'   \;  :    ; 
'--'.     /|  | ,'   ;  :   .'   \.'__/\_: |:  ,      .-./|  ,   /  
  `--'---' `--''     |  ,     .-./|   :    : `--`----'     ---`-'   
                      `--`---'     \   \  /                         
                                    `--`-'  
------------------------------------------------------------------
Function: List Associative arrays (object) in a GUI
Requires: Autohotkey_L 
URL: http://www.autohotkey.com/forum/viewtopic.php?t=68671
------------------------------------------------------------------
*/

;
; Function: Array_List
; Description:
;      GUI for showing contents of an associative array
; Syntax: Array_List(objArray, [Options])
; Parameters:
;      objArray - An associative array (object). Psuedo-arrays are not (yet) supported.
;      Options - Comma seperated options (see remarks)
; Return Value:
;      True on success, else false
; Remarks:
;      Options available are: 
;        Font - specify font as <font-options>:<font-name>, eg Font=s11 Bold:Arial [see http://www.autohotkey.net/~Lexikos/AutoHotkey_L/docs/commands/Gui.htm#Font]
;        GuiOptions - Gui options [see http://www.autohotkey.net/~Lexikos/AutoHotkey_L/docs/commands/Gui.htm#Options]
;        GuiShowOptions - Gui,Show options [see http://www.autohotkey.net/~Lexikos/AutoHotkey_L/docs/commands/Gui.htm#Show]
;        NoWait - Do not wait for the user to dismiss the dialog
; Example:
;      file:Example.ahk
;
Array_List(array,Options="") {
  if !IsObject(array) ;psuedo-arrays are not (yet) supported
    return 0

  global array_obj$
  if !IsObject(array_obj$)
    array_obj$ := Object()
  static Array_ListLV , objidx
  lastGUI := Array_DefaultGui()

  n := 50 ;find free gui after 50
  Loop 99 {
    n++
    Gui %n%:+LastFoundExist
    IfWinNotExist ;gui is free
      break
  }

  ;--- Default options
  GuiOptions := "+ToolWindow -SysMenu", GuiShowOptions := "w400 h400 center"
  
  ;--- Apply user defined options
  Loop, Parse, Options, `,, % A_Space
  {
    opt := Trim(SubStr(A_LoopField,1,InStr(A_LoopField,"=")-1)) 
    If (InStr("Font,GuiOptions,GuiShowOptions,NoWait",opt))
      %opt% := SubStr(A_LoopField,InStr(A_LoopField,"=") + 1,StrLen(A_LoopField))  
  }

  ;--- Create the GUI
  Gui, %n%: %GuiOptions% +LastFound
  if Font
    Gui, %n%:Font, % SubStr(Font,1,Pos := InStr(Font,":") - 1), % SubStr(Font,Pos + 2,StrLen(Font))  
  Gui, %n%:Show, w0 h0
  gui_id := WinExist()
  RegExMatch(GuiShowOptions,"\bw\K[0-9]+\b",w)
  RegExMatch(GuiShowOptions,"\bh\K[0-9]+\b",h)
  rows := array.GetCapacity()
  h -= 30 , x := (w/2)-25 
  Gui, %n%:Add, ListView, x0 y0 r%rows% w%w% h%h% vArray_ListLV gArray_ListDClick, Attribute|Value
  Gui, %n%:Add, Button, x%x% y+4 w50 h22 gArray_ButtonOK Default, &OK
  Gui, %n%:Default
  
  ;--- Add the data
  GuiControl, %n%: -Redraw, Array_ListLV
  Gui, %n%:ListView, Array_ListLV
  For attribute,value in array
  {
    If IsObject(value)
      {
      objidx++
      LV_Add("",attribute,"*object*" . objidx)
      array_obj$["obj" . objidx] := value
      }
    else
      LV_Add("",attribute,value)
  }
  GuiControl, %n%: +Redraw, Array_ListLV
  LV_ModifyCol()

  ;--- Showtime
  Gui, %n%:Show, %GuiShowOptions%, Array Data
  
  ;--- To wait or not to wait
  If Not NoWait
    WinWaitClose, ahk_id %gui_id%
  ; Else
  ;   SetTimer, Array_Timer, 500
  
  ;--- Reset global changes
  Gui, %lastGUI%: Default
  return 1
  
  Array_ListDClick:
  If (A_GuiEvent = "DoubleClick")
    {
    LV_GetText(LVvalue, A_EventInfo, 2)
    IfInString, LVvalue, *object*
      {
        idx := SubStr(LVvalue,InStr(LVvalue,"*",false,2)+1)
        Array_List(array_obj$["obj" . idx],Options)
      }
    }
  return

  Array_ButtonOK:
  GUI, %n%: Destroy
  return

}

;--- INTERNAL FUNCTION(S) ---;
Array_DefaultGui() { ;http://www.autohotkey.com/forum/viewtopic.php?t=26884 by majkinetor
  if A_Gui
  return A_GUI

  Gui, +LastFound
  m := DllCall( "RegisterWindowMessage", Str, "GETDEFGUI")
  OnMessage(m, "Array_DefaultGui")
  res := DllCall("SendMessage", "uint",  WinExist(), "uint", m, "uint", 0, "uint", 0)
  OnMessage(m, "")
  return res
}
