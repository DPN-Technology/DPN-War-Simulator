using UnrealBuildTool;
using System.Collections.Generic;
public class WarSimulatorUE5EditorTarget : TargetRules
{
    public WarSimulatorUE5EditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        ExtraModuleNames.Add("WarSimulatorUE5");
    }
}
