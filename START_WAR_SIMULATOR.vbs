Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "pyw -3 """ & base & "\WarSimulator.pyw"""
shell.Run cmd, 0, False
