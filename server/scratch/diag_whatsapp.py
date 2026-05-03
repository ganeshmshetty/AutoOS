import uiautomation as auto

whatsapp = auto.WindowControl(searchDepth=1, Name="WhatsApp")
if whatsapp.Exists(0):
    whatsapp.SetFocus()
    edits = whatsapp.EditControl(searchDepth=10)
    print(f"Found {len(edits.GetChildren())} top level edits? No, let's find all.")
    
    all_edits = whatsapp.WalkControl(lambda c, d: c.ControlTypeName == "EditControl")
    for i, edit in enumerate(all_edits):
        print(f"Edit {i}: Name='{edit.Name}', ID='{edit.AutomationId}'")
else:
    print("WhatsApp not found.")
