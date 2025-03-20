on run {volumeName}
  tell application "Finder"
    tell disk volumeName
      open
      set current view of container window to icon view
      set toolbar visible of container window to false
      set statusbar visible of container window to false
      set the bounds of container window to {200, 120, 1000, 720}
      set theViewOptions to the icon view options of container window
      set arrangement of theViewOptions to not arranged
      set icon size of theViewOptions to 100
      set background picture of theViewOptions to file ".background:Echelon_DMG_BG.png"
      set text size of theViewOptions to 14
      set text color of theViewOptions to {65535, 65535, 65535}
      delay 1
      update without registering applications
      delay 3
      close
    end tell
  end tell
end run
