using UnrealBuildTool;
using System.Collections.Generic;
public class WarSimulatorUE5Target : TargetRules
{
    public WarSimulatorUE5Target(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        ExtraModuleNames.Add("WarSimulatorUE5");
    }
}
