
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

pasta = FSO.GetParentFolderName(WScript.ScriptFullName)

WshShell.CurrentDirectory = pasta

WshShell.Run "cmd /c py manage.py runserver", 0, False

WScript.Sleep 5000

WshShell.Run "http://127.0.0.1:8000", 1, False

