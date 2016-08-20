; #Include, acc.ahk
; #Include, Array.ahk

f(a, value) {
	if (!IsObject(value)) {
		MsgBox % a . " Bad return value"
		exit
	}

	return value
}


GCR_EXE := "gcr_v1.0.exe"
; GCR_AHK := "ahk_exe " GCR_EXE		; spaces mandatory around dots
GCR_TITLE := "GCRebuilder v1.0"

SendMode Input

; **** Kill existing GCR processes.

RunWait, taskkill /f /im %GCR_EXE% ,,Hide
; read-only language ;)


; **** Start GCR.

Run, C:\Users\nyanpasu64\apps\gcr\gcr_v1.0.exe C:\Users\nyanpasu64\ROMS\lozww\lozww.iso, C:\Users\nyanpasu64\ROMS\lozww,
, gcr_pid
; MsgBox % gcr_pid
WinWait % GCR_TITLE

; command := ""
; ControlSend, %gcr_pid%, %command%, A
; ControlSend % gcr_pid, command, GCR_TITLE
Send audiores{right}seqs{right}jaiseqs.arc{appskey}i

WinWait Import file
Send {Enter}

WinWait Success
Send {Enter}

WinWaitActive % GCR_TITLE
Send +{Tab}{Enter}

Send !{F4}

Exit

; hwnd := WinExist(GCR_TITLE)
; if (!hwnd) {
; 	MsgBox % "WinExist '" GCR_TITLE "' broken?"
; 	return
; }












; ; **** Automate GCR.
; ; Acc_Init()
; win := f(1, Acc_ObjectFromWindow(hwnd))
; ; MsgBox % ComObjType(win, "Name")

; ; EVERYTHING is IAccessible!



; children := f(3, Acc_Children(win))

; ; MsgBox % isobject(children[1])
; ; Array_List(f(1337, children))

; For Each, widget in children {
; 	Array_List(Acc_Query(widget))
; 	; Array_List(Acc_Children(widget))
; 	; Array_List(widget)
; 		; 0x80020003 Member not found. _NewEnum https://autohotkey.com/boards/viewtopic.php?t=4524
; 		; So these are non-iterable objects????

; 	; MsgBox % ComObjType(widget, "Name")
; 		; IAccessible

; 	; Non-iterable IAccessible?
; 	; Array_List(Acc_Query(widget))

; 	; That's it. Fuck COM.

; 	; IRC?
; }
