' Crée un raccourci "eTrading" sur le Bureau Windows, pointant vers start-windows.bat
' A lancer UNE SEULE FOIS (double-clic) pour créer le raccourci.

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = fso.BuildPath(scriptDir, "start-windows.bat")
desktopPath = shell.SpecialFolders("Desktop")
shortcutPath = fso.BuildPath(desktopPath, "eTrading.lnk")

Set shortcut = shell.CreateShortcut(shortcutPath)
shortcut.TargetPath = batPath
shortcut.WorkingDirectory = scriptDir
shortcut.WindowStyle = 1
shortcut.Description = "Lancer le serveur eTrading en local"
shortcut.IconLocation = "shell32.dll,137"
shortcut.Save

MsgBox "Raccourci 'eTrading' créé sur le Bureau !" & vbCrLf & "Double-cliquez dessus pour lancer le bot.", 64, "eTrading"
