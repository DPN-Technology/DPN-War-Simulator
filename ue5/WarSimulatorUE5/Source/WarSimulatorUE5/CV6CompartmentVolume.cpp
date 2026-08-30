#include "CV6CompartmentVolume.h"

ACV6CompartmentVolume::ACV6CompartmentVolume(){ PrimaryActorTick.bCanEverTick=false; }
void ACV6CompartmentVolume::ApplySimState(float InFloodingPct, float InFireIntensity, float InSmokePct, bool bInPowered)
{
    FloodingPct=FMath::Clamp(InFloodingPct,0.f,100.f);
    FireIntensity=FMath::Clamp(InFireIntensity,0.f,100.f);
    SmokePct=FMath::Clamp(InSmokePct,0.f,100.f);
    bPowered=bInPowered;
}
