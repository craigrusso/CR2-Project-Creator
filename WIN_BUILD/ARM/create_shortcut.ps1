
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("Y:\WIN_BUILD\ARM\dist_final_dir\Echelon\Echelon.lnk")
        $Shortcut.TargetPath = "Y:\WIN_BUILD\ARM\dist_final_dir\Echelon\Echelon.exe"
        $Shortcut.IconLocation = "Y:\WIN_BUILD\ARM\dist_final_dir\Echelon\Echelon.exe,0"
        $Shortcut.WorkingDirectory = "Y:\WIN_BUILD\ARM\dist_final_dir\Echelon" # Set working directory
        $Shortcut.Save()
        